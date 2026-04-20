from pydantic import BaseModel
from datetime import datetime


class FraudScoreResponse(BaseModel):
    transaction_id: str
    risk_score: float
    fraud_label: str
    model_version: str
    scored_at: datetime
