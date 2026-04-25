from fastapi import APIRouter, Depends
from api.services.alert_service import get_alerts
from api.core.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("/")
async def fetch_alerts(
    current_user=Depends(require_role("admin"))
):
    alerts = await get_alerts()
    return {
        "alerts": alerts
    }