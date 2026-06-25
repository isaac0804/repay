from fastapi import FastAPI
from routers import wassist, paypal, mock_portal

app = FastAPI(title="Repay – Automated Delay Repay Agent", version="0.1.0")

app.include_router(wassist.router)
app.include_router(paypal.router)
app.include_router(mock_portal.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
