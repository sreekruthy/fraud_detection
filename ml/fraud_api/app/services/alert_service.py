import uuid
from datetime import datetime, timezone
from app.db.mongo import db


async def create_alert(
    transaction_id:  str,
    decision:        str,
    final_score:     float,
    rule_score:      float,
    ml_score:        float,
    explainability:  dict,
    user_id:         str,
    amount:          float,
    hold_expires_at: datetime | None = None,
    history_summary: dict | None     = None,
    auto_resolve:    bool             = False,
) -> str:
   
    now       = datetime.now(timezone.utc)
    alert_id  = str(uuid.uuid4())
    severity  = "CRITICAL" if decision == "FRAUD" else "HIGH"

    if auto_resolve:
        status       = "OPEN"
        admin_action = "AUTO_BLOCKED"
    else:
        status       = "OPEN"
        admin_action = None

    doc = {
        "alert_id":        alert_id,
        "transaction_id":  transaction_id,
        "user_id":         user_id,
        "decision":        decision,
        "severity":        severity,
        "status":          status,
        "admin_action":    admin_action,
        "final_score":     final_score,
        "rule_score":      rule_score,
        "ml_score":        ml_score,
        "amount":          amount,
        "explainability":  explainability,
        "hold_expires_at": hold_expires_at.isoformat() if hold_expires_at else None,
        "history_summary": history_summary,
        "created_at":      now,
        "updated_at":      now,
    }

    result = await db.alerts.insert_one(doc)
    print(f"  🚨 [{'CRITICAL' if decision == 'FRAUD' else 'HIGH'}] Alert created: {result.inserted_id}")
    return alert_id