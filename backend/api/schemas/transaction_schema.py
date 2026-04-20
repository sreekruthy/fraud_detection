from pydantic import BaseModel
from datetime import datetime


class TransactionCreate(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    location: str
    device_id: str
    timestamp: datetime


class TransactionResponse(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    location: str
    device_id: str
    timestamp: datetime
    risk_score: float | None = None
    fraud_label: str | None = None
