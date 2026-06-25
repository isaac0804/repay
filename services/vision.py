import base64
import json
import httpx
from config import settings
from models.schemas import TicketData

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-2.5-flash-lite:generateContent"
)

_PROMPT = (
    "You are a UK train ticket parser. Extract these fields from the ticket image: "
    "departure_station, arrival_station, scheduled_departure (ISO 8601), "
    "scheduled_arrival (ISO 8601), ticket_price (float, GBP), ticket_number. "
    "Return ONLY valid JSON with exactly these keys. Set any unreadable field to null."
)


async def parse_ticket_image(image_url: str) -> TicketData:
    async with httpx.AsyncClient(timeout=30) as client:
        # Download the image from Supabase Storage
        img_res = await client.get(image_url)
        img_res.raise_for_status()
        mime_type = img_res.headers.get("content-type", "image/jpeg").split(";")[0]
        image_b64 = base64.b64encode(img_res.content).decode()

        # Send to Gemini with inline image bytes
        response = await client.post(
            _GEMINI_URL,
            params={"key": settings.google_api_key},
            json={
                "contents": [{
                    "parts": [
                        {"text": _PROMPT},
                        {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                    ]
                }],
                "generationConfig": {"responseMimeType": "application/json"},
            },
        )
        response.raise_for_status()

    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return TicketData(**json.loads(text))
