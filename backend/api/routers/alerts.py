from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from api.services.alert_service import get_alerts, resolve_alert
from api.core.dependencies import get_current_user, require_role

router = APIRouter(tags=["Alerts"])


class ResolveRequest(BaseModel):
    transaction_id: str
    admin_action:   str


@router.get("/")
async def fetch_alerts(
    status: str | None = Query(None),
    current_user=Depends(require_role("admin"))
):
    alerts = await get_alerts(status=status)
    return {"total": len(alerts), "alerts": alerts}


@router.get("/open")
async def fetch_open_alerts(
    current_user=Depends(require_role("admin"))
):
    alerts = await get_alerts(status="OPEN")
    return {"total": len(alerts), "alerts": alerts}


@router.post("/resolve")
async def resolve_alert_route(
    req: ResolveRequest,
    current_user=Depends(require_role("admin"))
):
    ok = await resolve_alert(req.transaction_id, req.admin_action)
    return {"success": ok, "message": f"Alert {'resolved' if ok else 'not found or already resolved'}"}
