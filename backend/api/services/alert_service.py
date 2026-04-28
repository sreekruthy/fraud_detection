from database import mongo
from datetime import datetime, timezone


async def get_alerts(status: str | None = None) -> list[dict]:
    """
    Fetch alerts, optionally filtered by status.
    Called by /api/alerts/ and /api/alerts/open endpoints.

    status: "OPEN" | "RESOLVED" | None (returns all)
    """
    query = {}
    if status:
        query["status"] = status

    alerts = []
    cursor = mongo.db.alerts.find(query, {"_id": 0}).sort("created_at", -1)
    async for alert in cursor:
        # Serialize datetime fields
        for field in ("created_at", "updated_at", "hold_expires_at"):
            val = alert.get(field)
            if val is None:
                continue

            # datetime objects should be converted to ISO format strings for JSON serialization
            if hasattr(val, "isoformat"):
                dt = val if val.tzinfo else val.replace(tzinfo=timezone.utc)
                alert[field] = dt.isoformat()

            # already a string, but ensure it's in ISO format 
            elif isinstance(val, str) and val and not val.endswith("Z") and "+" not in val:
                alert[field] = val + "+00:00"
            
        alerts.append(alert)

    return alerts


async def resolve_alert(transaction_id: str, admin_action: str) -> bool:
    """
    Resolve an open alert after admin or user action.
    Returns True if an alert was found and updated.
    """
    result = await mongo.db.alerts.update_one(
        {"transaction_id": transaction_id, "status": "OPEN"},
        {"$set": {
            "status":       "RESOLVED",
            "admin_action": admin_action,
            "updated_at":   datetime.now(timezone.utc),
        }}
    )
    return result.modified_count > 0
