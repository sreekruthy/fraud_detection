"""
main.py
-------
Entry point. Keeps FastAPI routing clean and thin.
All logic lives in app/services/transaction_service.py
Run with:
    uvicorn main:app --reload --port 8000
"""

import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.services.transaction_service import create_transaction

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fraud Detection API",
    description="Receives a transaction, runs rule engine + ML model, saves to MongoDB.",
    version="2.0.0"
)
"""
main.py
-------
Entry point. Keeps FastAPI routing clean and thin.
All logic lives in app/services/transaction_service.py

Run with:
    uvicorn main:app --reload --port 8000
"""

import asyncio
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.services.transaction_service import create_transaction
from app.db.mongo import db

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fraud Detection API",
    description="Receives a transaction, runs rule engine + ML model, saves to MongoDB.",
    version="2.0.0"
)

# ── Pydantic schemas ──────────────────────────────────────────────────────────
class Location(BaseModel):
    city:      str
    country:   str
    latitude:  float
    longitude: float

class Device(BaseModel):
    ip:        str
    device_id: str
    browser:   str

class TransactionRequest(BaseModel):
    transaction_id: str
    user_id:        str
    amount:         float
    currency:       str = "USD"
    timestamp:      datetime
    location:       Location
    device:         Device
    receiver_id:    str
    user_home_city: Optional[str] = "New York"

# ── Expiry background task ────────────────────────────────────────────────────

async def expire_on_hold_transactions():
    """
    Runs every 60 seconds.
    Finds SUSPICIOUS transactions that are still ON_HOLD but whose
    hold_expires_at has passed — meaning the user never responded
    to the email in time. Flips them to FRAUD / BLOCKED automatically.
    """
    while True:
        try:
            now = datetime.now(timezone.utc)

            # Find all ON_HOLD transactions whose timer has expired
            expired = await db.transactions.find({
                "txn_status":     "ON_HOLD",
                "hold_expires_at": {"$lt": now}   # expires_at is in the past
            }).to_list(100)

            for txn in expired:
                txn_id = txn.get("transaction_id", str(txn["_id"]))

                # Flip transaction to BLOCKED
                await db.transactions.update_one(
                    {"transaction_id": txn_id},
                    {"$set": {
                        "txn_status":           "AWITING_ADMIN",
                        "customer_feedback":    "auto:expired",
                        "feedback_received_at": now,
                    }}
                )

                # Resolve the alert so admin dashboard shows it as handled
                await db.alerts.update_one(
                    {"transaction_id": txn_id, "status": "OPEN"},
                    {"$set": {
                        "admin_action": "AWAITING_ADMIN",
                        "updated_at":   now,
                    }}
                )

                print(f"  ⏰ EXPIRED: {txn_id} → AWAITING_ADMIN (admin must review)")

        except Exception as e:
            # Never let the background task crash the server
            print(f"  ⚠ Expiry task error: {e}")

        # Wait 60 seconds before checking again
        await asyncio.sleep(60)


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """
    Starts the expiry background task when the server boots.
    asyncio.create_task() runs it in the background without blocking.
    """
    asyncio.create_task(expire_on_hold_transactions())
    print("✅ Expiry background task started")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/transaction")
async def evaluate_transaction(request: TransactionRequest):
    """
    Submit a transaction for fraud detection.
    Runs rule engine + ML model, saves result to MongoDB, returns decision.
    """
    try:
        result = await create_transaction(request.model_dump())
        return result
    except Exception as e:
        traceback.print_exc()   # prints full stacktrace to uvicorn terminal
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
# ── Pydantic schemas ──────────────────────────────────────────────────────────
class Location(BaseModel):
    city:      str
    country:   str
    latitude:  float
    longitude: float

class Device(BaseModel):
    ip:        str
    device_id: str
    browser:   str

class TransactionRequest(BaseModel):
    transaction_id: str
    user_id:        str
    amount:         float
    currency:       str = "USD"
    timestamp:      datetime
    location:       Location
    device:         Device
    receiver_id:    str
    user_home_city: Optional[str] = "New York"

# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/transaction")
async def evaluate_transaction(request: TransactionRequest):
    """
    Submit a transaction for fraud detection.
    Runs rule engine + ML model, saves result to MongoDB, returns decision.
    """
    try:
        result = await create_transaction(request.model_dump())
        return result
    except Exception as e:
        traceback.print_exc()   # prints full stacktrace to uvicorn terminal
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}