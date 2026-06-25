from config import settings
from models.schemas import TicketData

# Refund thresholds per Rail Delivery Group Delay Repay rules
_REFUND_TIERS = [
    (120, 1.00),   # 2h+ → 100%
    (60,  0.50),   # 1h–2h → 50%
    (30,  0.25),   # 30–59 min → 25%
]

DEMO_DELAY_MINUTES = 45


def _calculate_refund(ticket_price: float, delay_minutes: int) -> float:
    for threshold, fraction in _REFUND_TIERS:
        if delay_minutes >= threshold:
            return round(ticket_price * fraction, 2)
    return 0.0


def check_train_delay(ticket: TicketData) -> tuple[int, float]:
    """Return (delay_minutes, refund_amount). In DEMO_MODE returns a hardcoded 45-min delay."""
    if settings.demo_mode:
        delay = DEMO_DELAY_MINUTES
        refund = _calculate_refund(ticket.ticket_price, delay)
        return delay, refund

    # TODO: replace with live National Rail / Darwin API call
    raise NotImplementedError("Live delay checking not yet implemented")
