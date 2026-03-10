from pydantic import BaseModel
from datetime import datetime


class LogModel(BaseModel):

    log_id: str
    action: str
    user_id: str | None = None
    timestamp: datetime
    details: str