import uuid
from fastapi import APIRouter, BackgroundTasks, Request

from config import settings
from models.schemas import WassistMessage, JourneyDetails
from services import supabase_client as db
from services import wassist, vision, delay, paypal, manus

router = APIRouter(prefix="/wassist", tags=["wassist"])


@router.post("/webhook")
async def wassist_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    msg = _parse_message(body)
    if msg is None:
        return {"status": "ignored"}

    background_tasks.add_task(_handle_message, msg)
    return {"status": "accepted"}


def _parse_message(body: dict) -> WassistMessage | None:
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        raw = entry["messages"][0]
        phone = raw["from"]
        if raw["type"] == "image":
            return WassistMessage(
                from_number=phone,
                message_type="image",
                media_id=raw["image"]["id"],
            )
        if raw["type"] == "text":
            return WassistMessage(
                from_number=phone,
                message_type="text",
                text=raw["text"]["body"].strip().upper(),
            )
    except (KeyError, IndexError):
        return None


async def _handle_message(msg: WassistMessage) -> None:
    if msg.message_type == "image":
        await _handle_image(msg)
    elif msg.message_type == "text":
        await _handle_text(msg)


async def _handle_image(msg: WassistMessage) -> None:
    phone = msg.from_number

    await wassist.send_message(phone, "Got your ticket! Analysing it now...")

    image_bytes = await wassist.download_media(msg.media_id)
    filename = f"{uuid.uuid4()}.jpg"
    image_url = await db.upload_image(image_bytes, filename)

    ticket = await vision.parse_ticket_image(image_url)
    delay_mins, refund = delay.check_train_delay(ticket)

    if delay_mins < 30:
        await wassist.send_message(
            phone,
            f"Your train was delayed by {delay_mins} minutes. "
            "Unfortunately that is below the 30-minute threshold for Delay Repay."
        )
        return

    journey = JourneyDetails(ticket=ticket, delay_minutes=delay_mins, refund_amount=refund)
    claim = await db.create_claim(phone, image_url, journey.model_dump())

    user = await db.get_user(phone)
    is_subscribed = settings.skip_paywall or (user and user.get("subscription_status"))

    if is_subscribed:
        await wassist.send_message(
            phone,
            f"Your train from {ticket.departure_station} to {ticket.arrival_station} "
            f"was delayed by {delay_mins} minutes. You are eligible for £{refund:.2f}. "
            "Reply YES to authorise the agent to file the claim on your behalf."
        )
    else:
        link = await paypal.create_subscription_link(phone)
        await wassist.send_message(
            phone,
            f"Good news! Your train was delayed by {delay_mins} mins. "
            f"You are owed £{refund:.2f}. Subscribe here to let our agent file "
            f"this and all future claims automatically (£4.99/month): {link}"
        )


async def _handle_text(msg: WassistMessage) -> None:
    phone = msg.from_number

    if msg.text == "YES":
        claim = await db.get_pending_claim(phone)
        if claim is None:
            await wassist.send_message(phone, "No pending claim found. Please send a photo of your ticket first.")
            return

        await db.update_claim_status(claim["id"], "approved")
        await wassist.send_message(phone, "Authorised! Filing your claim now...")

        journey = JourneyDetails(**claim["journey_details"])
        task_id = await manus.file_claim(journey, claim["ticket_image_url"])

        result = await manus.poll_until_complete(task_id)
        if result.get("agent_status") == "completed":
            await db.update_claim_status(claim["id"], "filed")
            refund = journey.refund_amount
            await wassist.send_message(
                phone,
                f"Claim submitted successfully! The transport operator will process "
                f"your £{refund:.2f} refund within 3–5 working days."
            )
        else:
            await db.update_claim_status(claim["id"], "failed")
            await wassist.send_message(
                phone,
                "Sorry, something went wrong while filing your claim. Our team has been notified."
            )

    elif msg.text in ("HELP", "SUPPORT"):
        await wassist.send_message(
            phone,
            "Need help? Reply with a photo of your train ticket to start a Delay Repay claim. "
            "For other support, contact support@repay.example.com."
        )
