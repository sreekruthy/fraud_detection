from fastapi import APIRouter
from app.services.alert_service import get_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/")
async def fetch_alerts():

    alerts = await get_alerts()

    return {
        "alerts": alerts
    }