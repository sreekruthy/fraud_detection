"""
main.py
-------
Entry point. Keeps FastAPI routing clean and thin.
All logic lives in app/services/transaction_service.py.

Run with:
    uvicorn main:app --reload
"""

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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}