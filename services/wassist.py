import httpx
from config import settings


async def send_message(to: str, text: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.wassist_base_url}/v1/messages",
            headers={"Authorization": f"Bearer {settings.wassist_api_key}"},
            json={"to": to, "type": "text", "text": {"body": text}},
            timeout=10,
        )
        response.raise_for_status()


async def download_media(media_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        # Step 1: resolve the media URL
        meta = await client.get(
            f"{settings.wassist_base_url}/v1/media/{media_id}",
            headers={"Authorization": f"Bearer {settings.wassist_api_key}"},
        )
        meta.raise_for_status()
        media_url = meta.json()["url"]

        # Step 2: download the binary
        download = await client.get(
            media_url,
            headers={"Authorization": f"Bearer {settings.wassist_api_key}"},
        )
        download.raise_for_status()
        return download.content
