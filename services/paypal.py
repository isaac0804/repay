import httpx
from config import settings

_token_cache: dict = {}


async def _get_access_token() -> str:
    if _token_cache.get("token"):
        return _token_cache["token"]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.paypal_base_url}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.paypal_client_id, settings.paypal_client_secret),
        )
        response.raise_for_status()

    data = response.json()
    _token_cache["token"] = data["access_token"]
    return data["access_token"]


async def create_subscription_link(phone_number: str) -> str:
    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.paypal_base_url}/v1/billing/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan_id": settings.paypal_plan_id,
                "custom_id": phone_number,
                "application_context": {
                    "return_url": "https://repay.example.com/paypal/return",
                    "cancel_url": "https://repay.example.com/paypal/cancel",
                },
            },
        )
        response.raise_for_status()

    links = response.json().get("links", [])
    approve_link = next((l["href"] for l in links if l["rel"] == "approve"), None)
    if not approve_link:
        raise ValueError("PayPal did not return an approval link")
    return approve_link
