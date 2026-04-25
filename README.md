# Fraud Detection System — v2.1 Flow Guide

## Core Difference: SUSPICIOUS vs FRAUD

| Feature                | SUSPICIOUS                           | FRAUD                              |
|------------------------|--------------------------------------|------------------------------------|
| txn_status on creation | `ON_HOLD`                            | `BLOCKED` (immediate)              |
| Hold window            | 2 minutes                            | None — blocked instantly           |
| Email purpose          | "Respond to hold your/cancel txn"    | "Your txn was blocked — was it you?" |
| Email banner           | 🟠 Orange HIGH RISK                  | 🔴 Red CRITICAL                    |
| Email CTA              | Yes/No → determines outcome          | Yes/No → for retraining only       |
| If YES                 | txn_status → CONFIRMED_LEGIT         | Reminder to redo transaction       |
| If NO                  | txn_status → BLOCKED                 | Account flagged, no action change  |
| Admin role             | Must decide if user doesn't respond  | Informed only (auto-blocked)       |
| Response token expiry  | ~7 minutes                           | 7 days                             |

---

## SUSPICIOUS Full Flow

```
1. ML model → final_score 0.50–0.70 → decision = "SUSPICIOUS"
2. Saved to DB: txn_status = "ON_HOLD", hold_expires_at = now + 120s
3. Alert created: severity=HIGH, hold_expires_at included, history_summary attached
4. Email sent: orange banner, 2-minute countdown, Yes/No buttons
5a. User responds in time:
      YES → txn_status = CONFIRMED_LEGIT, alert resolved
      NO  → txn_status = BLOCKED, alert resolved
5b. User doesn't respond (2 min passes):
      Admin dashboard shows "Window Expired — Admin Action Required"
      Admin sees user's transaction history summary (total txns, avg amount,
      fraud count, last 5 transactions) to make informed decision
      Admin clicks PERMIT → CONFIRMED_LEGIT
      Admin clicks BLOCK  → BLOCKED
```

---

## FRAUD Full Flow

```
1. ML model → final_score > 0.70 → decision = "FRAUD"
2. Saved to DB: txn_status = "BLOCKED" (immediate, no waiting)
3. Alert created: severity=CRITICAL, status=RESOLVED, admin_action=AUTO_BLOCKED
   (Alert is informational — no admin action needed)
4. Email sent AFTER blocking:
   - Red CRITICAL banner
   - "Your transaction of $X has been BLOCKED"
   - Shows: triggered rules, top features, risk score breakdown
   - "Was this you?"
5a. User says YES (legitimate):
      customer_feedback = "legitimate" (saved for retraining)
      txn_status stays BLOCKED
      Response: "Please redo your transaction — this one cannot be reversed"
5b. User says NO (fraud confirmed):
      customer_feedback = "fraud" (saved for retraining)
      txn_status stays BLOCKED
      Response: "Thank you — your account is being reviewed"
```

---

## customer_feedback Values & Retraining Strategy

| Value                 | Source              | Retraining Label |
|-----------------------|---------------------|------------------|
| `null`                | Legitimate txn      | implicit LEGIT   |
| `"legitimate"`        | User (SUSPICIOUS)   | LEGITIMATE       |
| `"fraud"`             | User (SUSPICIOUS)   | FRAUD            |
| `"legitimate"`        | User (FRAUD email)  | LEGITIMATE*      |
| `"fraud"`             | User (FRAUD email)  | FRAUD            |
| `"admin:PERMIT"`      | Admin action        | LEGITIMATE       |
| `"admin:BLOCK"`       | Admin action        | FRAUD            |
| `"analyst:LEGITIMATE"`| Analyst review      | LEGITIMATE       |

*For FRAUD txns where user says it was legitimate: treat as false positive in retraining.

**Retraining query:**
```python
# Get all labeled samples
labeled = db.transactions.find({
  "$or": [
    {"customer_feedback": {"$ne": None}},  # user/admin labeled
    {"decision": "LEGITIMATE"},            # implicit legitimate
  ]
})
# For null feedback on LEGITIMATE transactions: label = "LEGITIMATE"
# For null feedback on SUSPICIOUS/FRAUD: skip (no ground truth)
```

---

## New MongoDB Fields (transactions collection)

```json
{
  "txn_status":        "ON_HOLD",      // PROCESSED | ON_HOLD | BLOCKED | CONFIRMED_LEGIT
  "hold_expires_at":   "2026-04-22T...", // set for SUSPICIOUS only, null for FRAUD/LEGIT
  "alert_sent":        true,
  "email_sent":        true,
  "rule_score":        0.667,
  "ml_score":          0.923,
  "final_score":       0.846,
  "decision":          "FRAUD",
  "explainability":    { "triggered_rules": [...], "top_features": [...] },
  "customer_feedback": null,           // filled after user/admin responds
  "feedback_received_at": null
}
```

## New MongoDB Fields (alerts collection)

```json
{
  "severity":         "HIGH",          // CRITICAL (fraud) | HIGH (suspicious)
  "hold_expires_at":  "...",           // for SUSPICIOUS, null for FRAUD
  "history_summary":  { ... },         // for SUSPICIOUS, null for FRAUD
  "status":           "OPEN",          // OPEN | RESOLVED
  "admin_action":     null,            // set on resolution
  // AUTO_BLOCKED | PERMIT_USER_CONFIRMED | BLOCK_USER_CONFIRMED
  // ADMIN_PERMIT | ADMIN_BLOCK | PERMIT_ANALYST | BLOCK_ANALYST
}
```

---

## Setup

```bash
# Start MailHog (view emails at localhost:8025)
docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog

# ML Fraud API
cd ml/fraud_api && uvicorn main:app --reload --port 8000

# Main Backend
cd backend && uvicorn main:app --reload --port 5001

# Frontend
cd frontend && npm run dev   # port 5173

# Simulator (creates users + sends transactions)
python transaction_simulator.py
```

## Key .env variables (both services must share FEEDBACK_JWT_SECRET)

```
FEEDBACK_JWT_SECRET=same-value-in-both-services
FRONTEND_URL=http://localhost:5173
SMTP_HOST=localhost
SMTP_PORT=1025
```