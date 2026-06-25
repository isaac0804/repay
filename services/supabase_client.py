from supabase import create_client, Client
from config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


async def get_user(phone_number: str) -> dict | None:
    client = get_client()
    result = client.table("users").select("*").eq("phone_number", phone_number).maybe_single().execute()
    return result.data


async def upsert_user(phone_number: str, **kwargs) -> dict:
    client = get_client()
    data = {"phone_number": phone_number, **kwargs}
    result = client.table("users").upsert(data).execute()
    return result.data[0]


async def update_user_subscription(phone_number: str, paypal_sub_id: str) -> None:
    client = get_client()
    client.table("users").update({
        "subscription_status": True,
        "paypal_sub_id": paypal_sub_id,
    }).eq("phone_number", phone_number).execute()


async def create_claim(phone_number: str, ticket_image_url: str, journey_details: dict) -> dict:
    client = get_client()
    result = client.table("claims").insert({
        "phone_number": phone_number,
        "ticket_image_url": ticket_image_url,
        "journey_details": journey_details,
        "status": "pending",
        "estimated_refund": journey_details.get("refund_amount", 0),
    }).execute()
    return result.data[0]


async def update_claim_status(claim_id: str, status: str) -> None:
    client = get_client()
    client.table("claims").update({"status": status}).eq("id", claim_id).execute()


async def get_pending_claim(phone_number: str) -> dict | None:
    client = get_client()
    result = (
        client.table("claims")
        .select("*")
        .eq("phone_number", phone_number)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )
    return result.data


async def upload_image(file_bytes: bytes, filename: str) -> str:
    client = get_client()
    path = f"tickets/{filename}"
    client.storage.from_("ticket-images").upload(path, file_bytes, {"content-type": "image/jpeg"})
    public_url = client.storage.from_("ticket-images").get_public_url(path)
    return public_url
