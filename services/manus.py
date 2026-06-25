import asyncio
import httpx
from config import settings
from models.schemas import JourneyDetails

_POLL_INTERVAL = 10  # seconds between status checks
_MAX_POLLS = 60      # give up after 10 minutes


async def file_claim(journey: JourneyDetails, image_url: str) -> str:
    """Submit a claim task to Manus AI and return the task ID."""
    prompt = (
        f"Navigate to the Delay Repay portal at {settings.mock_delay_portal_url}. "
        f"Fill out the claim form using this information: "
        f"Departure station: {journey.ticket.departure_station}, "
        f"Arrival station: {journey.ticket.arrival_station}, "
        f"Scheduled departure: {journey.ticket.scheduled_departure}, "
        f"Ticket number: {journey.ticket.ticket_number}, "
        f"Ticket price: £{journey.ticket.ticket_price:.2f}. "
        f"Upload the ticket image from this URL: {image_url}. "
        f"Submit the form and confirm submission."
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.manus_base_url}/v2/task.create",
            headers={"x-manus-api-key": settings.manus_api_key},
            json={"prompt": prompt, "agentProfile": "manus-1.6"},
            timeout=30,
        )
        response.raise_for_status()

    return response.json()["task_id"]


# Terminal agent_status values reported by Manus v2
_TERMINAL_STATUSES = {"completed", "stopped", "failed"}


async def poll_until_complete(task_id: str) -> dict:
    """Poll the Manus task until it reaches a terminal state."""
    async with httpx.AsyncClient() as client:
        for _ in range(_MAX_POLLS):
            response = await client.get(
                f"{settings.manus_base_url}/v2/task.get",
                headers={"x-manus-api-key": settings.manus_api_key},
                params={"task_id": task_id},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("agent_status") in _TERMINAL_STATUSES:
                return data

            await asyncio.sleep(_POLL_INTERVAL)

    raise TimeoutError(f"Manus task {task_id} did not complete within the timeout")
