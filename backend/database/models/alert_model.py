from pydantic import BaseModel
from datetime import datetime


class AlertModel(BaseModel):

    alert_id: str
    transaction_id: str
    risk_score: float
    fraud_label: str
    created_at: datetime
