from pydantic import BaseModel
from datetime import datetime


class TransactionModel(BaseModel):

    transaction_id: str
    user_id: str
    amount: float
    location: str
    device_id: str
    timestamp: datetime

    # Fraud scoring fields (added later by fraud engine)
    risk_score: float | None = None
    fraud_label: str | None = None