from app.db.mongo import db
from datetime import datetime


async def store_feedback(feedback_data: dict):

    feedback_data["created_at"] = datetime.utcnow()

    result = await db.feedback.insert_one(feedback_data)

    return str(result.inserted_id)