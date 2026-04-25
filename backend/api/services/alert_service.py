from database import mongo
from datetime import datetime

async def get_alerts():
    alerts = []
    cursor = mongo.db.alerts.find({}, {"_id": 0})
    async for alert in cursor:
        alerts.append(alert)
    return alerts