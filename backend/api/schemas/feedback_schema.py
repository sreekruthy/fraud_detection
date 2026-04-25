from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    transaction_id: str
    analyst_decision: str
    comments: str | None = None
