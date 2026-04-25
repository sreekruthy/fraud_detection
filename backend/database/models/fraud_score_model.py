from pydantic import BaseModel
from datetime import datetime


class FraudScoreModel(BaseModel):

    transaction_id: str
    risk_score: float
    fraud_label: str
    model_version: str
    scored_at: datetime
