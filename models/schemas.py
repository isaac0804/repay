from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ClaimStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    filed = "filed"
    failed = "failed"


class TicketData(BaseModel):
    departure_station: str
    arrival_station: str
    scheduled_departure: str
    scheduled_arrival: str
    ticket_price: float
    ticket_number: str


class JourneyDetails(BaseModel):
    ticket: TicketData
    delay_minutes: int
    refund_amount: float


class WassistMessage(BaseModel):
    from_number: str
    message_type: str  # "text" | "image"
    text: Optional[str] = None
    image_url: Optional[str] = None
    media_id: Optional[str] = None


class PayPalWebhookEvent(BaseModel):
    event_type: str
    resource: dict
