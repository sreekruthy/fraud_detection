from database.mongo import db
from datetime import datetime, timezone


async def get_alerts(status: str | None = None) -> list[dict]:
    query = {}
    if status:
        query["status"] = status

    alerts = []
    async for alert in db.alerts.find(query, {"_id": 0}).sort("created_at", -1):
        for f in ("created_at", "updated_at", "hold_expires_at"):
            if f in alert and hasattr(alert[f], "isoformat"):
                alert[f] = alert[f].isoformat()
        alerts.append(alert)
    return alerts


async def resolve_alert(transaction_id: str, admin_action: str) -> bool:
    result = await db.alerts.update_one(
        {"transaction_id": transaction_id, "status": "OPEN"},
        {"$set": {
            "status":       "RESOLVED",
            "admin_action": admin_action,
            "updated_at":   datetime.now(timezone.utc),
        }}
    )
    return result.modified_count > 0