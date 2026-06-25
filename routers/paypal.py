from fastapi import APIRouter, Request

from models.schemas import PayPalWebhookEvent
from services import supabase_client as db
from services import wassist

router = APIRouter(prefix="/paypal", tags=["paypal"])


@router.post("/webhook")
async def paypal_webhook(event: PayPalWebhookEvent):
    if event.event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        sub = event.resource
        phone_number = sub.get("custom_id")
        sub_id = sub.get("id")

        if not phone_number or not sub_id:
            return {"status": "missing_data"}

        await db.update_user_subscription(phone_number, sub_id)
        await wassist.send_message(
            phone_number,
            "Subscription activated! Send a photo of any future delayed train ticket "
            "and we will file the claim automatically."
        )

    return {"status": "ok"}


@router.get("/return")
async def paypal_return(subscription_id: str | None = None):
    return {"message": "Subscription complete. You can close this tab and return to WhatsApp."}


@router.get("/cancel")
async def paypal_cancel():
    return {"message": "Subscription cancelled. You can still send ticket photos to start a claim."}
