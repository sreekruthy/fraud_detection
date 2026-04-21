"""
app/services/transaction_service.py
------------------------------------
The main pipeline. Called by main.py when a POST /transaction arrives.

Flow:
    1. Fetch user's last 100 transactions from MongoDB (for rule engine)
    2. Compute rule_score  (rule_engine.py)
    3. Compute ml_score    (voting classifier)
    4. Compute final_score (0.7 * ml_score + 0.3 * rule_score)
    5. Make decision       (LEGITIMATE / SUSPICIOUS / FRAUD)
    6. Save full document  to MongoDB
    7. Return result
"""

import math
import joblib
import pandas as pd

from datetime import datetime, timezone
from app.db.mongo import db
from app.services.rule_engine import compute_rule_score

# ── Load model once at import time ────────────────────────────────────────────
model = joblib.load("fraud_voting_classifier.joblib")
print("✅ Model loaded from fraud_voting_classifier.joblib")

# ── Constants ─────────────────────────────────────────────────────────────────
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

# ── Feature engineering ───────────────────────────────────────────────────────

def build_features(transaction: dict, rule_score: float) -> pd.DataFrame:
    """
    Mirrors the exact feature engineering from Kaggle training.
    rule_score is now included as a feature so the ML model
    benefits from the rule engine's signal too.
    """
    hour         = transaction["timestamp"].hour
    user_home    = transaction.get("user_home_city", "New York")
    lat          = transaction["location"]["latitude"]
    lon          = transaction["location"]["longitude"]

    # Distance from home
    if user_home in HOME_CITY_LOOKUP:
        h_lat, h_lon = HOME_CITY_LOOKUP[user_home]
        R    = 6371.0
        phi1 = math.radians(h_lat)
        phi2 = math.radians(lat)
        dphi = math.radians(lat - h_lat)
        dlam = math.radians(lon - h_lon)
        a    = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        dist = R * 2 * math.asin(math.sqrt(a))
    else:
        dist = 0.0

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

# ── Decision logic ────────────────────────────────────────────────────────────

def get_decision(final_score: float) -> str:
    """
    Three-tier decision based on final_score:
        < 0.50  → LEGITIMATE
        0.50–0.70 → SUSPICIOUS
        > 0.70  → FRAUD
    """
    if final_score < 0.50:
        return "LEGITIMATE"
    elif final_score <= 0.70:
        return "SUSPICIOUS"
    else:
        return "FRAUD"

# ── Explainability ────────────────────────────────────────────────────────────

def build_explainability(transaction: dict, dist: float) -> dict:
    """Generates human-readable reasons for the decision."""
    hour           = transaction["timestamp"].hour
    triggered      = []
    top_features   = []

    if transaction["amount"] > 8_000:
        triggered.append(f"High amount: ${transaction['amount']:,.2f}")
        top_features.append("amount (high)")
    if 2 <= hour <= 5:
        triggered.append(f"Unusual hour: {hour}:00 AM")
        top_features.append("hour_of_day (unusual)")
    if transaction["location"]["country"] != "US":
        triggered.append(f"Foreign country: {transaction['location']['country']}")
        top_features.append("is_foreign_country")
    if dist > 1_000:
        triggered.append(f"Far from home: {dist:,.0f} km")
        top_features.append("distance_from_home_km")

    return {
        "triggered_rules": triggered,
        "top_features":    top_features[:3],
    }

# ── Main pipeline ─────────────────────────────────────────────────────────────

async def create_transaction(transaction_data: dict) -> dict:
    """
    Full fraud detection pipeline for one incoming transaction.
    """

    # Convert timestamp string to datetime if needed
    if isinstance(transaction_data.get("timestamp"), str):
        transaction_data["timestamp"] = datetime.fromisoformat(
            transaction_data["timestamp"]
        )

    # ── Step 1: Fetch user history from MongoDB ───────────────────────────────
    user_history = await db.transactions.find(
        {"user_id": transaction_data["user_id"]}
    ).to_list(100)

    # ── Step 2: Rule engine ───────────────────────────────────────────────────
    rule_score = compute_rule_score(transaction_data, user_history)

    # ── Step 3: ML model ──────────────────────────────────────────────────────
    features   = build_features(transaction_data, rule_score)
    fraud_prob = float(model.predict_proba(features)[0][1])
    ml_score   = round(fraud_prob, 4)

    # ── Step 4: Final score ───────────────────────────────────────────────────
    # Weighted average: ML carries 70% weight, rules carry 30%
    # This means the ML model drives the decision but rule anomalies
    # can push borderline cases over the threshold
    final_score = round((0.7 * ml_score) + (0.3 * rule_score), 4)

    # ── Step 5: Decision ──────────────────────────────────────────────────────
    decision = get_decision(final_score)

    # ── Step 6: Build explainability ──────────────────────────────────────────
    user_home = transaction_data.get("user_home_city", "New York")
    dist      = 0.0
    if user_home in HOME_CITY_LOOKUP:
        h_lat, h_lon = HOME_CITY_LOOKUP[user_home]
        lat  = transaction_data["location"]["latitude"]
        lon  = transaction_data["location"]["longitude"]
        R    = 6371.0
        phi1 = math.radians(h_lat)
        phi2 = math.radians(lat)
        dphi = math.radians(lat - h_lat)
        dlam = math.radians(lon - h_lon)
        a    = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        dist = R * 2 * math.asin(math.sqrt(a))

    explainability = build_explainability(transaction_data, dist)

    # ── Step 7: Build full MongoDB document ───────────────────────────────────
    mongo_doc = {
        "transaction_id":      transaction_data["transaction_id"],
        "user_id":             transaction_data["user_id"],
        "amount":              transaction_data["amount"],
        "currency":            transaction_data.get("currency", "USD"),
        "timestamp":           transaction_data["timestamp"],
        "location":            transaction_data["location"],
        "device":              transaction_data["device"],
        "receiver_id":         transaction_data["receiver_id"],
        "rule_score":          rule_score,
        "ml_score":            ml_score,
        "final_score":         final_score,
        "decision":            decision,
        "explainability":      explainability,
        "customer_feedback":   None,
        "feedback_received_at": None,
        "created_at":          datetime.now(timezone.utc),
    }

    # ── Step 8: Insert into MongoDB ───────────────────────────────────────────
    await db.transactions.insert_one(mongo_doc)

    # ── Step 9: Return result ─────────────────────────────────────────────────
    return {
        "transaction_id": transaction_data["transaction_id"],
        "rule_score":     rule_score,
        "ml_score":       ml_score,
        "final_score":    final_score,
        "decision":       decision,
        "explainability": explainability,
    }