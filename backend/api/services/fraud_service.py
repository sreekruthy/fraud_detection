import random


# -----------------------------
# Fraud Risk Scoring
# -----------------------------
def calculate_risk_score(transaction):

    # Placeholder logic until ML model integration
    amount = transaction.get("amount", 0)

    if amount > 10000:
        risk_score = 0.9
    elif amount > 5000:
        risk_score = 0.6
    else:
        risk_score = random.uniform(0.1, 0.4)

    if risk_score > 0.8:
        label = "FRAUD"
    else:
        label = "SAFE"

    return {
        "risk_score": risk_score,
        "fraud_label": label
    }