"""
app/services/transaction_service.py
------------------------------------
Fraud detection pipeline with clearly differentiated flows:

SUSPICIOUS flow:
    - txn_status = "ON_HOLD"
    - Admin alert (severity=HIGH) includes user history summary + hold_expires_at
    - Email sent to user with a 2-minute countdown timer
    - If user responds in time → txn_status updated, alert resolved
    - If user does NOT respond in 2 min → admin dashboard shows "Expired, decide now"
      with full user history summary to help admin decide
    - Admin final call: PERMIT or BLOCK

FRAUD flow:
    - txn_status = "BLOCKED" immediately (no waiting, no user input needed to block)
    - Admin alert (severity=CRITICAL, auto-marked resolved with action=AUTO_BLOCKED)
    - AFTER blocking, email is sent to user:
        "Your transaction of $X was blocked due to fraud signals.
         Here's why: [triggered rules, scores].
         Was this actually you? If yes, please redo the transaction."
    - User response → saved to customer_feedback for retraining ONLY
    - Response does NOT unblock. Block is permanent.
"""

import math
import joblib
import pandas as pd

from datetime import datetime, timezone, timedelta
from app.db.mongo import db
from app.services.rule_engine import compute_rule_score
from app.services.alert_service import create_alert
from app.services.email_service import send_fraud_email, send_suspicious_email

# ── Load model once ───────────────────────────────────────────────────────────
model = joblib.load("fraud_voting_classifier.joblib")
print("✅ Model loaded from fraud_voting_classifier.joblib")

BROWSER_MAP = {"Chrome": 0, "Edge": 1, "Firefox": 2, "Safari": 3}

HOME_CITY_LOOKUP = {
    "New York":     (40.7128,  -74.0060),
    "Los Angeles":  (34.0522, -118.2437),
    "Chicago":      (41.8781,  -87.6298),
    "Houston":      (29.7604,  -95.3698),
    "Phoenix":      (33.4484, -112.0740),
    "Philadelphia": (39.9526,  -75.1652),
    "San Antonio":  (29.4241,  -98.4936),
    "San Diego":    (32.7157, -117.1611),
    "Dallas":       (32.7767,  -96.7970),
    "San Jose":     (37.3382, -121.8863),
}

# User gets 2 minutes to respond to a SUSPICIOUS email
SUSPICIOUS_WINDOW_SECONDS = 120


# ── Feature helpers ───────────────────────────────────────────────────────────

def haversine_dist(lat1, lon1, lat2, lon2) -> float:
    R    = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a    = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def get_home_dist(transaction: dict) -> float:
    user_home = transaction.get("user_home_city", "New York")
    lat = transaction["location"]["latitude"]
    lon = transaction["location"]["longitude"]
    if user_home in HOME_CITY_LOOKUP:
        h_lat, h_lon = HOME_CITY_LOOKUP[user_home]
        return haversine_dist(h_lat, h_lon, lat, lon)
    return 0.0


def build_features(transaction: dict, rule_score: float) -> pd.DataFrame:
    hour = transaction["timestamp"].hour
    dist = get_home_dist(transaction)
    return pd.DataFrame([{
        "amount":                transaction["amount"],
        "log_amount":            math.log1p(transaction["amount"]),
        "hour_of_day":           hour,
        "day_of_week":           transaction["timestamp"].weekday(),
        "is_unusual_hour":       int(2 <= hour <= 5),
        "distance_from_home_km": dist,
        "is_foreign_country":    int(transaction["location"]["country"] != "US"),
        "browser_encoded":       BROWSER_MAP.get(transaction["device"]["browser"], 0),
    }])


def get_decision(final_score: float) -> str:
    if final_score < 0.50:
        return "LEGITIMATE"
    elif final_score <= 0.70:
        return "SUSPICIOUS"
    else:
        return "FRAUD"


def build_explainability(transaction: dict) -> dict:
    hour      = transaction["timestamp"].hour
    dist      = get_home_dist(transaction)
    triggered = []
    top_feat  = []

    if transaction["amount"] > 8_000:
        triggered.append(f"High amount: ${transaction['amount']:,.2f}")
        top_feat.append("amount (high)")
    if 2 <= hour <= 5:
        triggered.append(f"Unusual hour: {hour}:00 AM")
        top_feat.append("hour_of_day (unusual)")
    if transaction["location"]["country"] != "US":
        triggered.append(f"Foreign country: {transaction['location']['country']}")
        top_feat.append("is_foreign_country")
    if dist > 1_000:
        triggered.append(f"Far from home: {dist:,.0f} km")
        top_feat.append("distance_from_home_km")

    return {"triggered_rules": triggered, "top_features": top_feat[:3]}


async def get_user_history_summary(user_id: str) -> dict:
    """
    Builds a brief summary of the user's past transactions.
    Attached to SUSPICIOUS alerts so admin can make informed decisions
    when the user fails to respond within the 2-minute window.
    """
    txns = await db.transactions.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(50)

    if not txns:
        return {
            "total": 0, "avg_amount": 0,
            "fraud_count": 0, "suspicious_count": 0,
            "avg_risk_score": 0, "recent": []
        }

    amounts       = [t.get("amount", 0) for t in txns]
    risk_scores   = [t.get("final_score", 0) for t in txns]
    fraud_count   = sum(1 for t in txns if t.get("decision") == "FRAUD")
    susp_count    = sum(1 for t in txns if t.get("decision") == "SUSPICIOUS")

    recent = []
    for t in txns[:5]:
        recent.append({
            "transaction_id": t.get("transaction_id"),
            "amount":         t.get("amount"),
            "decision":       t.get("decision"),
            "final_score":    t.get("final_score"),
            "location":       t.get("location", {}).get("city", "Unknown"),
            "timestamp":      (
                t["timestamp"].isoformat()
                if hasattr(t.get("timestamp"), "isoformat")
                else str(t.get("timestamp", ""))
            ),
        })

    return {
        "total":            len(txns),
        "avg_amount":       round(sum(amounts) / len(amounts), 2),
        "fraud_count":      fraud_count,
        "suspicious_count": susp_count,
        "avg_risk_score":   round(sum(risk_scores) / len(risk_scores), 4),
        "recent":           recent,
    }


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def create_transaction(transaction_data: dict) -> dict:

    if isinstance(transaction_data.get("timestamp"), str):
        transaction_data["timestamp"] = datetime.fromisoformat(
            transaction_data["timestamp"]
        )

    # ── Scores ────────────────────────────────────────────────────────────────
    user_history = await db.transactions.find(
        {"user_id": transaction_data["user_id"]}
    ).to_list(100)

    rule_score  = compute_rule_score(transaction_data, user_history)
    features    = build_features(transaction_data, rule_score)
    fraud_prob  = float(model.predict_proba(features)[0][1])
    ml_score    = round(fraud_prob, 4)
    final_score = round((0.7 * ml_score) + (0.3 * rule_score), 4)
    decision    = get_decision(final_score)
    explain     = build_explainability(transaction_data)

    now = datetime.now(timezone.utc)

    # ── txn_status ────────────────────────────────────────────────────────────
    # FRAUD      → BLOCKED immediately (admin + ML decision, final)
    # SUSPICIOUS → ON_HOLD (waits for user response, then admin decides)
    # LEGITIMATE → PROCESSED
    if decision == "FRAUD":
        txn_status = "BLOCKED"
    elif decision == "SUSPICIOUS":
        txn_status = "ON_HOLD"
    else:
        txn_status = "PROCESSED"

    hold_expires_at = (
        now + timedelta(seconds=SUSPICIOUS_WINDOW_SECONDS)
        if decision == "SUSPICIOUS" else None
    )

    # ── Save to DB ────────────────────────────────────────────────────────────
    mongo_doc = {
        "transaction_id":       transaction_data["transaction_id"],
        "user_id":              transaction_data["user_id"],
        "amount":               transaction_data["amount"],
        "currency":             transaction_data.get("currency", "USD"),
        "timestamp":            transaction_data["timestamp"],
        "location":             transaction_data["location"],
        "device":               transaction_data["device"],
        "receiver_id":          transaction_data["receiver_id"],
        "rule_score":           rule_score,
        "ml_score":             ml_score,
        "final_score":          final_score,
        "decision":             decision,
        "txn_status":           txn_status,
        "explainability":       explain,
        # hold_expires_at: set for SUSPICIOUS, tells dashboard when window closes
        "hold_expires_at":      hold_expires_at,
        "customer_feedback":    None,
        "feedback_received_at": None,
        "alert_sent":           False,
        "email_sent":           False,
        "created_at":           now,
    }

    await db.transactions.insert_one(mongo_doc)
    print(f"✅ Saved {transaction_data['transaction_id']} → {decision} ({txn_status})")

    # ── Post-save: fetch user for email ───────────────────────────────────────
    user       = await db.users.find_one({"user_id": transaction_data["user_id"]})
    user_email = user.get("email") if user else None
    user_name  = user.get("name", "User") if user else "User"

    if decision == "SUSPICIOUS":
        await _handle_suspicious(
            transaction_data, mongo_doc, explain,
            final_score, user_email, user_name, hold_expires_at
        )

    elif decision == "FRAUD":
        await _handle_fraud(
            transaction_data, mongo_doc, explain,
            final_score, rule_score, ml_score,
            user_email, user_name
        )

    return {
        "transaction_id": transaction_data["transaction_id"],
        "rule_score":     rule_score,
        "ml_score":       ml_score,
        "final_score":    final_score,
        "decision":       decision,
        "txn_status":     txn_status,
        "explainability": explain,
    }


# ── SUSPICIOUS handler ────────────────────────────────────────────────────────

async def _handle_suspicious(
    transaction_data, mongo_doc, explain,
    final_score, user_email, user_name, hold_expires_at
):
    txn_id = transaction_data["transaction_id"]

    # Attach user history to alert — admin needs this to decide if user doesn't respond
    history_summary = await get_user_history_summary(transaction_data["user_id"])

    try:
        await create_alert(
            transaction_id  = txn_id,
            decision        = "SUSPICIOUS",
            final_score     = final_score,
            rule_score      = mongo_doc["rule_score"],
            ml_score        = mongo_doc["ml_score"],
            explainability  = explain,
            user_id         = transaction_data["user_id"],
            amount          = transaction_data["amount"],
            hold_expires_at = hold_expires_at,
            history_summary = history_summary,
            auto_resolve    = False,
        )
        await db.transactions.update_one(
            {"transaction_id": txn_id}, {"$set": {"alert_sent": True}}
        )
        print(f"  🔔 SUSPICIOUS alert created for {txn_id}, expires at {hold_expires_at}")
    except Exception as e:
        print(f"  ⚠ Alert failed: {e}")

    if user_email:
        try:
            await send_suspicious_email(
                user_email              = user_email,
                user_name               = user_name,
                transaction_id          = txn_id,
                amount                  = transaction_data["amount"],
                location                = transaction_data["location"],
                timestamp               = transaction_data["timestamp"],
                explainability          = explain,
                final_score             = final_score,
                response_window_seconds = SUSPICIOUS_WINDOW_SECONDS,
            )
            await db.transactions.update_one(
                {"transaction_id": txn_id}, {"$set": {"email_sent": True}}
            )
            print(f"  📧 SUSPICIOUS email sent → {user_email}")
        except Exception as e:
            print(f"  ⚠ Email failed: {e}")


# ── FRAUD handler ─────────────────────────────────────────────────────────────

async def _handle_fraud(
    transaction_data, mongo_doc, explain,
    final_score, rule_score, ml_score,
    user_email, user_name
):
    txn_id = transaction_data["transaction_id"]

    try:
        # Fraud alerts are auto-resolved: transaction is already blocked.
        # Admin is notified but does NOT need to take action.
        await create_alert(
            transaction_id  = txn_id,
            decision        = "FRAUD",
            final_score     = final_score,
            rule_score      = rule_score,
            ml_score        = ml_score,
            explainability  = explain,
            user_id         = transaction_data["user_id"],
            amount          = transaction_data["amount"],
            hold_expires_at = None,
            history_summary = None,
            auto_resolve    = True,   # auto-resolved, no admin action needed
        )
        await db.transactions.update_one(
            {"transaction_id": txn_id}, {"$set": {"alert_sent": True}}
        )
        print(f"  🚨 FRAUD alert created (auto-resolved/blocked) for {txn_id}")
    except Exception as e:
        print(f"  ⚠ Alert failed: {e}")

    if user_email:
        try:
            # Email sent AFTER blocking — informational + retraining data collection
            await send_fraud_email(
                user_email     = user_email,
                user_name      = user_name,
                transaction_id = txn_id,
                amount         = transaction_data["amount"],
                location       = transaction_data["location"],
                timestamp      = transaction_data["timestamp"],
                explainability = explain,
                final_score    = final_score,
            )
            await db.transactions.update_one(
                {"transaction_id": txn_id}, {"$set": {"email_sent": True}}
            )
            print(f"  📧 FRAUD (post-block) email sent → {user_email}")
        except Exception as e:
            print(f"  ⚠ Fraud email failed: {e}")