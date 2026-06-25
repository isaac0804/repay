from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["mock-portal"])

_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Delay Repay – Demo Portal</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }
  label { display: block; margin: 12px 0 4px; font-weight: 600; }
  input, select { width: 100%; padding: 8px; box-sizing: border-box; }
  button { margin-top: 20px; padding: 10px 24px; background: #1a73e8; color: #fff; border: none;
           border-radius: 4px; cursor: pointer; font-size: 1rem; }
  .success { background: #e6f4ea; border: 1px solid #34a853; padding: 16px; border-radius: 4px; }
</style>
</head>
<body>
<h1>Delay Repay Claim Portal <small style="color:#888;font-size:.6em">(DEMO)</small></h1>
<form method="post" action="/mock-portal/submit" enctype="multipart/form-data">
  <label>Departure station</label>
  <input name="departure_station" required>
  <label>Arrival station</label>
  <input name="arrival_station" required>
  <label>Scheduled departure</label>
  <input name="scheduled_departure" type="datetime-local" required>
  <label>Ticket number</label>
  <input name="ticket_number" required>
  <label>Ticket price (£)</label>
  <input name="ticket_price" type="number" step="0.01" min="0" required>
  <label>Ticket image</label>
  <input name="ticket_image" type="url" placeholder="https://…" required>
  <button type="submit">Submit Claim</button>
</form>
</body>
</html>
"""

_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Claim Submitted</title>
<style>body {{ font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
.success {{ background: #e6f4ea; border: 1px solid #34a853; padding: 24px; border-radius: 4px; }}</style>
</head>
<body>
<div class="success">
  <h2>Claim submitted successfully!</h2>
  <p><strong>Reference:</strong> DEMO-{ref}</p>
  <p>Journey: {departure} → {arrival}</p>
  <p>Ticket: {ticket_number} | Price: £{price}</p>
  <p>The operator will respond within 3–5 working days.</p>
</div>
</body>
</html>
"""


@router.get("/mock-portal", response_class=HTMLResponse)
async def mock_portal():
    return HTMLResponse(_FORM_HTML)


@router.post("/mock-portal/submit", response_class=HTMLResponse)
async def mock_portal_submit(
    departure_station: str = Form(...),
    arrival_station: str = Form(...),
    scheduled_departure: str = Form(...),
    ticket_number: str = Form(...),
    ticket_price: float = Form(...),
    ticket_image: str = Form(...),
):
    import random, string
    ref = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    html = _SUCCESS_HTML.format(
        ref=ref,
        departure=departure_station,
        arrival=arrival_station,
        ticket_number=ticket_number,
        price=f"{ticket_price:.2f}",
    )
    return HTMLResponse(html)
