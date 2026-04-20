from fastapi import APIRouter
from api.schemas.feedback_schema import FeedbackCreate
from api.services.feedback_service import store_feedback

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("/")
async def submit_feedback(feedback: FeedbackCreate):

    feedback_data = feedback.dict()

    feedback_id = await store_feedback(feedback_data)

    return {
        "message": "Feedback stored",
        "feedback_id": feedback_id
    }
