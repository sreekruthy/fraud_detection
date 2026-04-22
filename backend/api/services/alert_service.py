from datetime import datetime, timezone
from api.db.mongo import db


async def create_alert(
    transaction_id: str,
    decision: str,
    final_score: float,
    rule_score: float,
    ml_score: float,
    explainability: dict,
    user_id: str,
    amount: float,
    hold_expires_at=None,
    history_summary: dict | None = None,
    auto_resolve: bool = False,
) -> str:

    severity = "CRITICAL" if decision == "FRAUD" else "HIGH"
    now      = datetime.now(timezone.utc)

    triggered = explainability.get("triggered_rules", [])
    summary   = f"{severity} alert: {decision} — ${amount:,.2f} by {user_id}."
    if triggered:
        summary += " Flags: " + "; ".join(triggered[:3])

    alert_doc = {
        "transaction_id":   transaction_id,
        "user_id":          user_id,
        "decision":         decision,
        "severity":         severity,
        "final_score":      final_score,
        "rule_score":       rule_score,
        "ml_score":         ml_score,
        "amount":           amount,
        "explainability":   explainability,
        "summary":          summary,
        # SUSPICIOUS: hold window + user history for admin reference
        "hold_expires_at":  hold_expires_at,
        "history_summary":  history_summary,
        # FRAUD: auto-resolved immediately
        "status":           "RESOLVED" if auto_resolve else "OPEN",
        "admin_action":     "AUTO_BLOCKED" if auto_resolve else None,
        "created_at":       now,
        "updated_at":       now,
    }

    result   = await db.alerts.insert_one(alert_doc)
    alert_id = str(result.inserted_id)
    print(f"  🚨 [{severity}] Alert created: {alert_id}")
    return alert_id


async def get_all_alerts(status: str | None = None) -> list[dict]:
    query = {}
    if status:
        query["status"] = status

    alerts = []
    async for alert in db.alerts.find(query).sort("created_at", -1):
        alert["_id"] = str(alert["_id"])
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