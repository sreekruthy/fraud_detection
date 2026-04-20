from database.db.mongo import db
from datetime import datetime


# -----------------------------
# Create Alert
# -----------------------------
async def create_alert(transaction_id, risk_score, fraud_label):

    alert_data = {
        "transaction_id": transaction_id,
        "risk_score": risk_score,
        "fraud_label": fraud_label,
        "created_at": datetime.utcnow()
    }

    result = await db.alerts.insert_one(alert_data)

    return str(result.inserted_id)


# -----------------------------
# Get Alerts
# -----------------------------
async def get_alerts():

    alerts = []

    cursor = db.alerts.find({}, {"_id": 0})

    async for alert in cursor:
        alerts.append(alert)

    return alerts
