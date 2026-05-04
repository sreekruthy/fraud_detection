import math
import statistics
from datetime import datetime, timezone, timedelta

TIME_WINDOW_DAYS = 30


def _to_utc(dt) -> datetime:
    if dt is None:
        return dt
    if not isinstance(dt, datetime):
        return dt
    if dt.tzinfo is None:
        # MongoDB stores naive UTC datetimes — treat as UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# Haversine distance 

def haversine(lat1, lon1, lat2, lon2):
    """Returns great-circle distance in km between two coordinates."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# Rule engine 

def compute_rule_score(transaction: dict, user_history: list) -> float:
    """
    Computes a rule-based fraud score from 0.0 to 1.0.

    Args:
        transaction  : the current incoming transaction as a dict
        user_history : list of past transaction dicts for this user

    Returns:
        float between 0.0 and 1.0
    """
    score     = 0
    max_score = 3

    now = _to_utc(transaction.get("timestamp"))
    if not now:
        return 0.0

    # Filter to last 30 days only — normalize each history timestamp before comparing
    recent_history = [
        t for t in user_history
        if now - _to_utc(t["timestamp"]) <= timedelta(days=TIME_WINDOW_DAYS)
    ]

    # If no history exists yet, we can't compute anomalies — return 0
    if not recent_history:
        return 0.0

    # Rule 1: Amount anomaly 
    # If this transaction's amount is more than 2 standard deviations
    # above the user's recent average, it's statistically unusual.
    amounts = [t["amount"] for t in recent_history]
    if len(amounts) > 1:
        avg = statistics.mean(amounts)
        std = statistics.stdev(amounts)
        if std > 0:
            z_score = (transaction["amount"] - avg) / std
            if z_score > 2:
                score += 1

    # Rule 2: Location anomaly 
    # If the average distance from this transaction to all recent transactions
    # is greater than 500 km, the user is transacting far from usual.
    try:
        distances = [
            haversine(
                transaction["location"]["latitude"],
                transaction["location"]["longitude"],
                t["location"]["latitude"],
                t["location"]["longitude"]
            )
            for t in recent_history if "location" in t
        ]
        if distances and statistics.mean(distances) > 500:
            score += 1
    except Exception:
        pass

    # Rule 3: Time anomaly 
    # If this transaction's hour is more than 6 hours away from the user's
    # average transaction hour, it's happening at an unusual time.
    txn_hour   = now.hour
    past_hours = [_to_utc(t["timestamp"]).hour for t in recent_history]
    avg_hour   = statistics.mean(past_hours)
    if abs(txn_hour - avg_hour) > 6:
        score += 1

    return round(score / max_score, 3)