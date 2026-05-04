# FraudGuard — Real-Time Fraud Detection System

> An end-to-end fraud detection platform: transactions are scored by an ML ensemble, passed through a rule engine, stored in MongoDB, and surfaced on a live React dashboard — with email alerts fired automatically on suspicious activity.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [ML Model](#ml-model)
- [MongoDB Structure](#mongodb-structure)
- [Environment Setup](#environment-setup)
- [Running the System (5 Terminals)](#running-the-system-5-terminals)
- [Transaction Simulator](#transaction-simulator)
- [API Reference](#api-reference)
- [Test Accounts](#test-accounts)
- [Admin Setup](#admin-setup)
- [Troubleshooting](#troubleshooting)

---

## System Architecture

```
┌──────────────────────────┐
│   transaction_simulator  │  Seeds users + POSTs synthetic transactions
│   (project root CLI)     │  3 types: legit / suspicious / fraud
└────────────┬─────────────┘
             │  POST /transaction
             ▼
┌──────────────────────────┐
│   ML Fraud API           │  Port 8000
│   ml/fraud_api/main.py   │──── rule_engine.py ──→ flags by amount/hour/location
│                          │──── fraud_voting_classifier.joblib → ML score
│                          │──── transaction_service.py → final decision
│                          │──── alert_service.py → writes alert to MongoDB
│                          │──── email_service.py → sends email via MailHog
└────────────┬─────────────┘
             │  Writes to MongoDB Atlas
             ▼
┌──────────────────────────┐     ┌────────────────────────────────────┐
│   Backend API            │     │   MongoDB Atlas                    │
│   backend/api/main.py    │────▶│   DB: FraudDetection               │
│   Port 8001              │     │                                    │
│                          │     │   collections:                     │
│   Routers:               │     │   - admins                         │
│   /api/transactions      │     │   - alerts                         │
│   /api/alerts            │     │   - fraud_results                  │
│   /api/auth              │     │   - transactions                   │
│   /api/feedback          │     │   - users                          │
└────────────┬─────────────┘     └────────────────────────────────────┘
             │
             ▼
┌──────────────────────────┐     ┌────────────────────────────┐
│   React Frontend         │     │   MailHog                  │
│   Port 5173              │     │   Port 8025                │
│                          │     │                            │
│   Pages:                 │     │   Catches all outbound     │
│   - Dashboard            │     │   SMTP emails in dev.      │
│   - FlaggedTransactions  │     │   No real emails sent.     │
│   - Transaction          │     └────────────────────────────┘
│   - VerifyTransaction    │
│   - Login                │
└──────────────────────────┘
```

---

## Project Structure

```
fraud-detection/
│
├── transaction_simulator.py      # CLI — seeds users + fires test transactions
├── docker-compose.yml            # Spins up MailHog
├── requirements.txt
│
├── ml/
│   └── fraud_api/
│       ├── main.py               # FastAPI entry point (port 8000)
│       │                         # POST /transaction → runs rule engine + ML
│       │                         # Background task: auto-expires ON_HOLD txns
│       ├── fraud_voting_classifier.joblib   # Trained ensemble model
│       ├── .env                  # MONGO_URI (see Environment Setup)
│       ├── requirements.txt
│       └── app/
│           ├── db/mongo.py
│           └── services/
│               ├── transaction_service.py   # Orchestrates the full pipeline
│               ├── rule_engine.py           # Pre-ML rule-based scoring
│               ├── alert_service.py         # Creates alerts in MongoDB
│               └── email_service.py         # Sends fraud alert emails
│
├── backend/
│   ├── .env                      # All backend config (see Environment Setup)
│   ├── api/
│   │   ├── main.py               # FastAPI entry point (port 8001)
│   │   ├── routers/
│   │   │   ├── transaction.py    # GET/POST /api/transactions
│   │   │   ├── alerts.py         # GET /api/alerts
│   │   │   ├── auth.py           # POST /api/auth/login etc.
│   │   │   └── feedback.py       # POST /api/feedback
│   │   ├── schemas/
│   │   │   ├── transaction_schema.py
│   │   │   ├── alert_schema.py
│   │   │   ├── fraud_score_schema.py
│   │   │   ├── user_schema.py
│   │   │   └── auth_schema.py
│   │   ├── services/
│   │   │   ├── transaction_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── fraud_service.py
│   │   │   ├── email_service.py
│   │   │   ├── auth_service.py
│   │   │   └── feedback_service.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   └── utils/logger.py
│   ├── database/
│   │   ├── mongo.py              # Motor async MongoDB connection
│   │   └── models/
│   │       ├── transaction_model.py
│   │       ├── alert_model.py
│   │       ├── user_model.py
│   │       ├── fraud_score_model.py
│   │       ├── admin_model.py
│   │       └── log_model.py
│   └── create_admin.py           # One-time script to create admin accounts
│
└── frontend/
    └── src/
        ├── App.jsx
        ├── api/axiosConfig.js
        ├── components/
        │   ├── Navbar.jsx
        │   └── Sidebar.jsx
        └── pages/
            ├── Dashboard.jsx
            ├── FlaggedTransactions.jsx
            ├── Transaction.jsx
            ├── VerifyTransaction.jsx
            └── Login.jsx
```

---

## How It Works

### Transaction Lifecycle

Every transaction submitted to the ML API goes through this exact pipeline:

```
POST /transaction
      │
      ▼
1. Rule Engine  (rule_engine.py)
   Flags based on:
   - Amount thresholds
   - Transaction hour (late night = higher risk)
   - Location vs. user's home city
   └── produces: rule_score (0.0 – 1.0)
      │
      ▼
2. ML Voting Classifier
   fraud_voting_classifier.joblib
   Ensemble of Random Forest + XGBoost + LightGBM
   └── produces: ml_score (0.0 – 1.0)
      │
      ▼
3. Final Decision  (transaction_service.py)
   Combines rule_score + ml_score → final_score
   └── decision: LEGITIMATE | SUSPICIOUS | FRAUD
      │
      ├── LEGITIMATE → saved to MongoDB, no alert
      │
      ├── SUSPICIOUS → saved + alert created + email sent to user
      │               txn_status: ON_HOLD
      │               user has a time window to confirm/deny via email link
      │               Background task checks every 60s:
      │               if hold_expires_at passed → AWAITING_ADMIN
      │
      └── FRAUD      → saved + alert created + email sent
                       txn_status: BLOCKED
```

### ON_HOLD Expiry (Background Task)

The ML API runs a background coroutine (`expire_on_hold_transactions`) that wakes every 60 seconds. It finds `SUSPICIOUS` transactions where `hold_expires_at` has passed — meaning the user never responded to the alert email in time — and automatically escalates them to `AWAITING_ADMIN` so an admin can review from the dashboard.

---

## ML Model

The fraud scoring model is a **Voting Classifier** ensemble stored as `fraud_voting_classifier.joblib`:

| Base Model | Type | Why included |
|---|---|---|
| Random Forest | Bagging | Robust to noise, low variance, handles non-linear patterns |
| XGBoost | Gradient Boosting | High accuracy on tabular data, handles class imbalance |
| LightGBM | Gradient Boosting | Fast inference, efficient on high-dimensional features |

All three models vote on each transaction. The final `ml_score` is derived from the combined probability output. Using an ensemble reduces overfitting and lowers false positives compared to any single model — critical in fraud detection where false positives directly erode user trust.

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

## MongoDB Structure

**Cluster:** `frauddetectioncluster`  
**Database:** `FraudDetection`  
**Collections:** `admins`, `alerts`, `fraud_results`, `transactions`, `users`

---

### `transactions`

One document per transaction. Written by the ML API after scoring.

```json
{
  "transaction_id": "TXN_304C97256A",
  "user_id":        "USR_001",
  "amount":         22076.56,
  "currency":       "USD",
  "timestamp":      "2026-04-28T02:35:16.037+00:00",
  "location":       { "city": "...", "country": "...", "latitude": 0.0, "longitude": 0.0 },
  "device":         { "ip": "...", "device_id": "...", "browser": "..." },
  "receiver_id":    "RCV_015",
  "rule_score":     0,
  "ml_score":       1,
  "final_score":    0.7,
  "decision":       "SUSPICIOUS",
  "txn_status":     "BLOCKED",
  "explainability": {},
  "hold_expires_at":"2026-04-28T17:40:16.077+00:00",
  "customer_feedback":    "fraud",
  "feedback_received_at": "2026-04-28T17:36:43.190+00:00",
  "alert_sent":     true,
  "email_sent":     true,
  "created_at":     "2026-04-28T17:35:16.077+00:00"
}
```

---

### `alerts`

One document per flagged transaction (SUSPICIOUS or FRAUD). Updated as the case progresses.

```json
{
  "alert_id":       "ffd1db3c-19ea-4c77-8985-cdc67c2a1219",
  "transaction_id": "TXN_304C97256A",
  "user_id":        "USR_001",
  "decision":       "SUSPICIOUS",
  "severity":       "HIGH",
  "status":         "RESOLVED",
  "admin_action":   "BLOCK_USER_CONFIRMED",
  "final_score":    0.7,
  "rule_score":     0,
  "ml_score":       1,
  "amount":         22076.56,
  "explainability": {},
  "history_summary":{},
  "hold_expires_at":"2026-04-28T17:40:16.077+00:00",
  "created_at":     "2026-04-28T17:35:16.144+00:00",
  "updated_at":     "2026-04-28T17:36:43.213+00:00"
}
```

**`status` values:** `OPEN` → `RESOLVED`  
**`admin_action` values:** `BLOCK_USER_CONFIRMED`, `AWAITING_ADMIN`, etc.

---

### `fraud_results`

Raw ML model output stored per transaction, separate from the business decision.

```json
{
  "original_id":    "69a8753fa8b5e2f5d517c30f",
  "transaction_id": "TXN0",
  "amount":         149.62,
  "ml_score":       0.0579,
  "classification": "Normal",
  "action":         "Approve transaction"
}
```

---

### `users`

Seeded by `transaction_simulator.py --users-only`. Updated over time as transactions accumulate.

```json
{
  "user_id":                "USR_003",
  "name":                   "Carol White",
  "email":                  "carol@mailhog.test",
  "password":               "<bcrypt hash>",
  "home_city":              "Chicago",
  "account_created_at":     "2026-04-22T13:08:25.298+00:00",
  "avg_transaction_amount": 0,
  "transaction_frequency":  0,
  "historical_risk_score":  0
}
```

`home_city` is used by the rule engine to detect geographic anomalies. `avg_transaction_amount`, `transaction_frequency`, and `historical_risk_score` are updated as the user transacts — which is why `rule_score` starts at `0` for new users.

---

### `admins`

Created manually via `create_admin.py`. Credentials are hardcoded in the script before running.

```json
{
  "admin_id":            "ADM12",
  "name":                "Axis Admin",
  "email":               "abc@axis.com",
  "password_hash":       "<bcrypt hash>",
  "role":                "admin",
  "created_at":          "2026-02-01",
  "must_change_password": true
}
```

---

## Environment Setup

There are **two separate `.env` files** — one for each Python service. Create both before starting the system.

---

### `ml/fraud_api/.env`

Used by the ML API and the transaction simulator (the simulator reads this file automatically from the project root).

```env
MONGO_URI=mongodb+srv://<username>:<password>@frauddetectioncluster.xetemzc.mongodb.net/?appName=frauddetectioncluster
```

| Variable | Description |
|---|---|
| `MONGO_URI` | Full MongoDB Atlas connection string. Replace `<username>` and `<password>` with your Atlas credentials. |

---

### `backend/.env`

Used by the Backend API only.

```env
# ─ MongoDB ─
MONGO_URL=mongodb+srv://<username>:<password>@frauddetectioncluster.xetemzc.mongodb.net/?appName=frauddetectioncluster
DATABASE_NAME=FraudDetection

# ─ Frontend URL ─
# Used to build the verify/feedback link inside alert emails
FRONTEND_URL=http://localhost:5173

# ─ JWT Secrets ─
# Both must match across email_service.py and feedback.py
FEEDBACK_JWT_SECRET=feedbacksecretkey
JWT_SECRET_KEY=supersecretkeyabcdefghij123   # must be exactly 32 characters

# ─ SMTP / MailHog ─
# MailHog catches all emails locally — no real emails are sent
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASS=
SMTP_FROM=alerts@fraudsystem.com
SMTP_USE_TLS=false
```

| Variable | Description |
|---|---|
| `MONGO_URL` | Full MongoDB Atlas connection string |
| `DATABASE_NAME` | Must be `FraudDetection` to match the Atlas database |
| `FRONTEND_URL` | Where the React app runs — used to build email verify links |
| `FEEDBACK_JWT_SECRET` | Signs tokens embedded in feedback email links |
| `JWT_SECRET_KEY` | Must be exactly 32 characters. Used for auth token signing |
| `SMTP_HOST` / `SMTP_PORT` | Points to MailHog in dev (`localhost:1025`) |
| `SMTP_FROM` | The sender address shown in alert emails |
| `SMTP_USE_TLS` | Keep `false` for MailHog. Set `true` for production SMTP |

> **Note:** `SMTP_USER` and `SMTP_PASS` are intentionally left blank — MailHog does not require authentication.

---

## Running the System (5 Terminals)

Start services in this order. **The ML API (Terminal 2) must be running before you send transactions.**

---

### Terminal 1 — Docker (MailHog)

```bash
# From project root
docker compose up -d
```

Starts MailHog on port 8025. All outbound fraud alert emails land here in development.

```bash
# To stop MailHog
docker stop fraud_mailhog
```

> **MailHog UI**: http://localhost:8025

---

### Terminal 2 — ML Fraud API (port 8000)

The core scoring engine. Runs the rule engine, ML model, writes to MongoDB, fires emails, and manages the ON_HOLD expiry background task.

```bash
cd ml/fraud_api
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> **Swagger docs**: http://127.0.0.1:8000/docs

---

### Terminal 3 — Backend API (port 8001)

Handles auth, transaction history, alerts, and analyst feedback for the dashboard.

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn api.main:app --reload --port 8001
```

> **Swagger docs**: http://127.0.0.1:8001/docs

---

### Terminal 4 — Frontend Dashboard (port 5173)

```bash
cd frontend
npm run dev
```

> **Dashboard**: http://localhost:5173

---

### Terminal 5 — Transaction Simulator

```bash
# From project root

# First time / fresh DB: seed users into MongoDB
python3 transaction_simulator.py --users -only

# Send 10 transactions
python3 transaction_simulator.py --count 10

# Default: 30 transactions
python3 transaction_simulator.py
```

---

## Transaction Simulator

`transaction_simulator.py` seeds 8 test users into MongoDB then fires synthetic transactions at the ML API with a weighted mix of patterns.

### Transaction Types

| Type | Amount Range | Hour | Location | Expected Decision |
|---|---|---|---|---|
| `legit` | $20 – $1,500 | 9am – 6pm | US cities | LEGITIMATE |
| `suspicious` | $5,000 – $8,000 | 10pm – midnight | US cities | SUSPICIOUS |
| `fraud` | $15,000 – $50,000 | 2am – 5am | Lagos / Bucharest / Bangkok / Minsk | FRAUD |

Live output per transaction:

```
  [01/10] FRAUD        | TXN_4F8A2C | USR_003 | $32,450.00 | Lagos, NG  →  FRAUD (0.94)  [BLOCKED]
  [02/10] LEGIT        | TXN_9B1D7E | USR_001 |    $340.00 | New York, US  →  LEGITIMATE (0.11)  [APPROVED]
```

> **Note:** The first few transactions per user show `rule_score=0` — expected. The rule engine builds from `avg_transaction_amount`, `transaction_frequency`, and `historical_risk_score` in the users collection, which start at `0` for new users.

The simulator aborts automatically after 5 consecutive connection errors if the ML API is unreachable.

---

## API Reference

### ML API — `http://127.0.0.1:8000`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/transaction` | Submit a transaction for fraud scoring |
| `GET` | `/health` | Returns `{"status": "ok", "version": "2.0.0"}` |
| `GET` | `/docs` | Swagger UI |

**POST `/transaction` — Request body:**

```json
{
  "transaction_id": "TXN_ABC123",
  "user_id":        "USR_001",
  "amount":         25000.00,
  "currency":       "USD",
  "timestamp":      "2026-04-28T03:22:00Z",
  "location": {
    "city":      "Lagos",
    "country":   "NG",
    "latitude":  6.5244,
    "longitude": 3.3792
  },
  "device": {
    "ip":        "192.168.4.21",
    "device_id": "DEV_USR_001_2",
    "browser":   "Chrome"
  },
  "receiver_id":    "RCV_007",
  "user_home_city": "New York"
}
```

**Response:**

```json
{
  "decision":   "FRAUD",
  "final_score": 0.94,
  "txn_status": "BLOCKED"
}
```

---

### Backend API — `http://127.0.0.1:8001`

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/api/transactions` | List or query transactions |
| `GET` | `/api/alerts` | Fetch fraud alerts |
| `POST` | `/api/auth/login` | Analyst / admin login |
| `POST` | `/api/feedback` | Submit analyst feedback on a flagged transaction |
| `GET` | `/` | Health check — `{"status": "healthy"}` |
| `GET` | `/docs` | Swagger UI |

---

## Test Accounts

After running `--users-only`, all 8 users are available in the `users` collection:

| User ID | Email | Home City | Password |
|---|---|---|---|
| USR_001 | alice@mailhog.test | New York | test1234 |
| USR_002 | bob@mailhog.test | Los Angeles | test1234 |
| USR_003 | carol@mailhog.test | Chicago | test1234 |
| USR_004 | david@mailhog.test | Houston | test1234 |
| USR_005 | eva@mailhog.test | Phoenix | test1234 |
| USR_006 | frank@mailhog.test | San Jose | test1234 |
| USR_007 | grace@mailhog.test | Dallas | test1234 |
| USR_008 | henry@mailhog.test | Philadelphia | test1234 |

---

## Admin Setup

Admin accounts are **not seeded automatically**. They must be created manually via `create_admin.py`. Open the file, set the `admin_id`, `name`, `email`, `password`, and `role` fields directly in the script, then run:

```bash
cd backend
source venv/bin/activate
python create_admin.py
```

The password is stored as a bcrypt hash in the `admins` collection. The `must_change_password` flag is set to `true` on creation — the admin will be prompted to change their password on first login.

To add another admin, edit the credentials in `create_admin.py` and run it again.

---

## Troubleshooting

**`rule_score` is 0 for first transactions**

Expected — the rule engine uses `avg_transaction_amount`, `transaction_frequency`, and `historical_risk_score` from the users collection, which start at `0`. Run `--count 30` first to build up history.



**Simulator can't reach ML API**
```
Cannot connect to ML API at http://localhost:8000/transaction
```
Terminal 2 must be running before the simulator is started. The simulator aborts after 5 consecutive connection failures.



**`MONGO_URI` not found**

The simulator exits immediately if `MONGO_URI` is missing from `ml/fraud_api/.env`. Make sure the file exists at that exact path (not the project root `.env`).



**MailHog not receiving emails**
```bash
docker ps | grep mailhog     # confirm it's running
docker compose up -d         # restart if needed
```
Then visit http://localhost:8025.



**Port already in use**
```bash
lsof -ti:8000 | xargs kill -9    # ML API
lsof -ti:8001 | xargs kill -9    # Backend API
```



**Frontend CORS errors from backend** 

The ML API allows all origins in development. If the dashboard (port 5173) can't reach the backend API (port 8001), check that the backend CORS config includes `http://localhost:5173`.



**`JWT_SECRET_KEY` errors**

The key must be exactly 32 characters. Count carefully — shorter or longer will cause auth failures.

---

