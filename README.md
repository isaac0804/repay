# Repay

Automated UK train Delay Repay agent via WhatsApp. Users send a photo of their train ticket; the agent parses it, checks the delay, and files a compensation claim on their behalf.

## How it works

```
User (WhatsApp)
    │  sends ticket photo
    ▼
Wassist (WhatsApp gateway)  →  POST /wassist/webhook
    │
    ├─ Gemini 2.5 Flash Lite parses ticket → departure, arrival, price, times
    ├─ Delay check (DEMO_MODE: hardcoded 45 min | real: National Rail API)
    ├─ Applies Rail Delivery Group refund tiers:
    │    30–59 min → 25%  |  60–119 min → 50%  |  120 min+ → 100%
    │
    ├─ delay < 30 min  →  "Below threshold" reply, done
    ├─ not subscribed  →  PayPal subscription link (£4.99/month)
    └─ subscribed      →  "Reply YES to authorise"

User replies "YES"
    │
    ├─ Manus AI agent drives the claim portal form
    └─ WhatsApp reply: "Filed! Expect £X in 3–5 working days"
```

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + uvicorn |
| WhatsApp | Wassist |
| Vision / OCR | Google Gemini 2.5 Flash Lite |
| Claim filing | Manus AI (browser agent) |
| Payments | PayPal sandbox subscriptions |
| Database | Supabase (PostgreSQL + Storage) |
| Deployment | Render (`render.yaml` included) |

## Project structure

```
main.py                   # FastAPI app, mounts routers
config.py                 # Settings from .env via pydantic-settings
models/
  schemas.py              # Pydantic models (TicketData, JourneyDetails, …)
routers/
  wassist.py              # Webhook handler — core orchestration
  paypal.py               # Subscription webhook + return/cancel pages
  mock_portal.py          # Self-contained HTML claim form for demos
services/
  vision.py               # Gemini vision — ticket image → TicketData JSON
  delay.py                # Delay check + refund tier calculation
  manus.py                # Manus AI task creation + polling
  paypal.py               # PayPal OAuth + subscription link
  supabase_client.py      # DB helpers (users, claims, image storage)
  wassist.py              # Send messages + download media
supabase/
  schema.sql              # Run this in the Supabase SQL editor once
```

## Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Description |
|---|---|
| `WASSIST_API_KEY` | From your Wassist dashboard |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `GOOGLE_API_KEY` | Google AI Studio key (Gemini) |
| `MANUS_API_KEY` | Manus AI API key |
| `PAYPAL_CLIENT_ID` | PayPal sandbox app credentials |
| `PAYPAL_CLIENT_SECRET` | PayPal sandbox app credentials |
| `PAYPAL_PLAN_ID` | Pre-created £4.99/month billing plan ID |
| `DEMO_MODE` | `true` — hardcodes 45-min delay; `false` — calls National Rail API (not yet implemented) |
| `SKIP_PAYWALL` | `true` — skips PayPal subscription check (useful for testing) |
| `MOCK_DELAY_PORTAL_URL` | URL Manus navigates to when filing claims |

### 3. Initialise the database

Run `supabase/schema.sql` in the Supabase SQL editor. Also create the storage bucket via the Supabase dashboard:

- Bucket name: `ticket-images`
- Public: yes

### 4. Run the server

```bash
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`.

## Demo (no WhatsApp needed)

Set in `.env`:

```env
DEMO_MODE=true
SKIP_PAYWALL=true
```

Start the server and browse the mock claim portal:

```
http://localhost:8000/mock-portal
```

## Full WhatsApp demo

Your server must be publicly reachable so Wassist can POST to the webhook.

```bash
ngrok http 8000
```

Set the resulting URL as your webhook in the Wassist dashboard:

```
https://<your-ngrok-id>.ngrok-free.app/wassist/webhook
```

Then send a photo of a train ticket to the WhatsApp number linked to your Wassist account.

## Deployment (Render)

`render.yaml` is included. Connect the repo in the Render dashboard and set the environment variables listed above — Render will build and deploy automatically.

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/wassist/webhook` | Wassist inbound message webhook |
| `POST` | `/paypal/webhook` | PayPal subscription event webhook |
| `GET` | `/paypal/return` | PayPal post-subscription redirect |
| `GET` | `/paypal/cancel` | PayPal cancellation redirect |
| `GET` | `/mock-portal` | Demo claim form |
| `POST` | `/mock-portal/submit` | Demo claim form submission |
| `GET` | `/health` | Health check |

## Refund tiers

Per Rail Delivery Group Delay Repay rules:

| Delay | Refund |
|---|---|
| Under 30 minutes | None |
| 30–59 minutes | 25% of ticket price |
| 60–119 minutes | 50% of ticket price |
| 120 minutes or more | 100% of ticket price |
