"""
app/services/alert_service.py  (ML API layer)
----------------------------------------------
Creates alerts in MongoDB when a transaction is flagged SUSPICIOUS or FRAUD.
This is the ML-layer service — it WRITES alerts.

The main backend layer (api/services/alert_service.py) READS and resolves them.

Called by transaction_service.py after every flagged transaction.
"""

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
    """
    Insert an alert document into MongoDB.

    SUSPICIOUS alerts:
      - severity = HIGH
      - status   = OPEN  (admin must act after user responds / window expires)
      - hold_expires_at set to when the 5-min user window closes
      - history_summary attached so admin has context if user doesn't respond

    FRAUD alerts:
      - severity = CRITICAL
      - status   = RESOLVED  (auto-resolved — transaction already blocked)
      - admin_action = "AUTO_BLOCKED"
      - No hold window, no history needed

    Returns the alert_id string.
    """
    now       = datetime.now(timezone.utc)
    alert_id  = str(uuid.uuid4())
    severity  = "CRITICAL" if decision == "FRAUD" else "HIGH"

    if auto_resolve:
        status       = "RESOLVED"
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