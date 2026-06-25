import httpx
import json
from config import settings
from models.schemas import TicketData

SYSTEM_PROMPT = (
    "You are a UK train ticket parser. Extract the following fields from the ticket image: "
    "departure_station, arrival_station, scheduled_departure (ISO 8601), scheduled_arrival (ISO 8601), "
    "ticket_price (float, GBP), ticket_number. Return ONLY valid JSON with these exact keys. "
    "If a field cannot be read, set it to null."
)


async def parse_ticket_image(image_url: str) -> TicketData:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.deepseek_base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "model": "deepseek-v4-flash",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url}},
                            {"type": "text", "text": "Parse this train ticket."},
                        ],
                    },
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    return TicketData(**data)
