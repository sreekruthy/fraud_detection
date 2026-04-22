"""
transaction_simulator.py
------------------------
Simulates realistic transactions for the fraud detection system.

What this does:
  1. Creates a pool of users in MongoDB (with email + bcrypt password)
     so you can log in to check your verification email in MailHog.
  2. Sends batches of transactions to the ML Fraud API (port 8000).
  3. Uses repeated user_ids so rule engine has history to work with.
  4. Mixes LEGITIMATE, SUSPICIOUS, and FRAUD-like patterns.

Run AFTER starting:
  - MailHog:  docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
  - ML API:   cd ml/fraud_api && uvicorn main:app --reload --port 8000
  - Backend:  cd backend && uvicorn main:app --reload --port 5001

Usage:
  python transaction_simulator.py               # run full simulation
  python transaction_simulator.py --users-only  # only seed users
  python transaction_simulator.py --count 20    # send 20 transactions
"""

import asyncio
import argparse
import random
import uuid
import bcrypt
from datetime import datetime, timezone, timedelta

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI")
DB_NAME    = os.getenv("DB_NAME", "FraudDetection")
ML_API     = "http://localhost:8000/transaction"
PASSWORD   = "test1234"   # All test users share this password for easy testing

client = AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]

# ── User pool — repeated users so history builds up ───────────────────────────
# Same user_ids used across multiple transactions → rule engine gets richer signal
USER_POOL = [
    {"user_id": "USR_001", "name": "Alice Johnson",  "email": "alice@mailhog.test",   "home_city": "New York"},
    {"user_id": "USR_002", "name": "Bob Smith",      "email": "bob@mailhog.test",     "home_city": "Los Angeles"},
    {"user_id": "USR_003", "name": "Carol White",    "email": "carol@mailhog.test",   "home_city": "Chicago"},
    {"user_id": "USR_004", "name": "David Lee",      "email": "david@mailhog.test",   "home_city": "Houston"},
    {"user_id": "USR_005", "name": "Eva Martinez",   "email": "eva@mailhog.test",     "home_city": "Phoenix"},
    {"user_id": "USR_006", "name": "Frank Kim",      "email": "frank@mailhog.test",   "home_city": "San Jose"},
    {"user_id": "USR_007", "name": "Grace Patel",    "email": "grace@mailhog.test",   "home_city": "Dallas"},
    {"user_id": "USR_008", "name": "Henry Brown",    "email": "henry@mailhog.test",   "home_city": "Philadelphia"},
]

# ── Location presets ──────────────────────────────────────────────────────────
NORMAL_LOCATIONS = [
    {"city": "New York",     "country": "US", "latitude": 40.7128,  "longitude": -74.0060},
    {"city": "Los Angeles",  "country": "US", "latitude": 34.0522,  "longitude": -118.2437},
    {"city": "Chicago",      "country": "US", "latitude": 41.8781,  "longitude": -87.6298},
    {"city": "Houston",      "country": "US", "latitude": 29.7604,  "longitude": -95.3698},
    {"city": "Phoenix",      "country": "US", "latitude": 33.4484,  "longitude": -112.0740},
    {"city": "Philadelphia", "country": "US", "latitude": 39.9526,  "longitude": -75.1652},
    {"city": "Dallas",       "country": "US", "latitude": 32.7767,  "longitude": -96.7970},
    {"city": "San Jose",     "country": "US", "latitude": 37.3382,  "longitude": -121.8863},
]

SUSPICIOUS_LOCATIONS = [
    {"city": "Miami",        "country": "US", "latitude": 25.7617,  "longitude": -80.1918},
    {"city": "Seattle",      "country": "US", "latitude": 47.6062,  "longitude": -122.3321},
    {"city": "Denver",       "country": "US", "latitude": 39.7392,  "longitude": -104.9903},
]

FRAUD_LOCATIONS = [
    {"city": "Lagos",        "country": "NG", "latitude": 6.5244,   "longitude": 3.3792},
    {"city": "Bucharest",    "country": "RO", "latitude": 44.4268,  "longitude": 26.1025},
    {"city": "Minsk",        "country": "BY", "latitude": 53.9045,  "longitude": 27.5615},
    {"city": "Bangkok",      "country": "TH", "latitude": 13.7563,  "longitude": 100.5018},
]

BROWSERS = ["Chrome", "Firefox", "Safari", "Edge"]
RECEIVER_IDS = [f"RCV_{i:03d}" for i in range(1, 20)]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Seed users ────────────────────────────────────────────────────────────────

async def seed_users():
    """
    Insert users into MongoDB if they don't already exist.
    Each user gets an email + bcrypt-hashed password so you can
    log in to MailHog and then use the verify link in the email.
    """
    print("\n👥 Seeding users…")
    created = 0
    for u in USER_POOL:
        existing = await db.users.find_one({"user_id": u["user_id"]})
        if existing:
            print(f"  ⏭  {u['user_id']} already exists")
            continue

        doc = {
            "user_id":               u["user_id"],
            "name":                  u["name"],
            "email":                 u["email"],
            "password":              hash_password(PASSWORD),
            "home_city":             u["home_city"],
            "account_created_at":    datetime.now(timezone.utc).isoformat(),
            "avg_transaction_amount": 0,
            "transaction_frequency":  0,
            "historical_risk_score":  0.0,
        }
        await db.users.insert_one(doc)
        print(f"  ✅ Created {u['user_id']} ({u['name']}) → {u['email']} / password: {PASSWORD}")
        created += 1

    print(f"  Done. {created} new users created.\n")


# ── Build transaction payloads ─────────────────────────────────────────────────

def _txn_id() -> str:
    return f"TXN_{uuid.uuid4().hex[:10].upper()}"


def _device(user_id: str) -> dict:
    return {
        "ip":        f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
        "device_id": f"DEV_{user_id}_{random.randint(1,5)}",
        "browser":   random.choice(BROWSERS),
    }


def make_legitimate_txn(user: dict) -> dict:
    """Normal transaction — low amount, US location, daytime hour."""
    # Pick a location close to home city
    loc = random.choice(NORMAL_LOCATIONS)
    ts  = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60))
    # Normal hour: 8am–8pm
    ts  = ts.replace(hour=random.randint(8, 20))

    return {
        "transaction_id": _txn_id(),
        "user_id":        user["user_id"],
        "amount":         round(random.uniform(20, 2000), 2),
        "currency":       "USD",
        "timestamp":      ts.isoformat(),
        "location":       loc,
        "device":         _device(user["user_id"]),
        "receiver_id":    random.choice(RECEIVER_IDS),
        "user_home_city": user["home_city"],
    }


def make_suspicious_txn(user: dict) -> dict:
    """Medium-risk transaction — higher amount OR unusual location."""
    loc = random.choice(SUSPICIOUS_LOCATIONS)
    ts  = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 10))
    # Mix of hours including some late
    ts  = ts.replace(hour=random.choice([0, 1, 23, 22] + list(range(8, 20))))

    return {
        "transaction_id": _txn_id(),
        "user_id":        user["user_id"],
        "amount":         round(random.uniform(4000, 7000), 2),  # elevated
        "currency":       "USD",
        "timestamp":      ts.isoformat(),
        "location":       loc,
        "device":         _device(user["user_id"]),
        "receiver_id":    random.choice(RECEIVER_IDS),
        "user_home_city": user["home_city"],
    }


def make_fraud_txn(user: dict) -> dict:
    """High-risk transaction — large amount, foreign country, unusual hour."""
    loc = random.choice(FRAUD_LOCATIONS)
    ts  = datetime.now(timezone.utc)
    ts  = ts.replace(hour=random.randint(2, 5))  # unusual hour: 2–5 AM

    return {
        "transaction_id": _txn_id(),
        "user_id":        user["user_id"],
        "amount":         round(random.uniform(12000, 50000), 2),
        "currency":       "USD",
        "timestamp":      ts.isoformat(),
        "location":       loc,
        "device":         _device(user["user_id"]),
        "receiver_id":    random.choice(RECEIVER_IDS),
        "user_home_city": user["home_city"],
    }


# ── Send transaction to ML API ────────────────────────────────────────────────

async def send_transaction(client_http: httpx.AsyncClient, txn: dict) -> dict | None:
    try:
        res = await client_http.post(ML_API, json=txn, timeout=15.0)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"    ❌ Failed to send {txn['transaction_id']}: {e}")
        return None


# ── Main simulation ────────────────────────────────────────────────────────────

async def run_simulation(total: int = 30):
    """
    Sends `total` transactions.
    Mix: ~60% legit, ~25% suspicious-pattern, ~15% fraud-pattern.
    Repeated user_ids ensure history builds up for the rule engine.

    Note: The ML model makes the final call — these are patterns,
    not guaranteed labels. A "fraud_pattern" might still score below 0.7.
    """
    await seed_users()

    print(f"🚀 Sending {total} transactions to {ML_API}…\n")

    # Build a weighted list of (user, type) pairs
    # Use repeated users heavily — rule engine needs history
    patterns = (
        [(u, "legit")      for u in USER_POOL] * 6 +
        [(u, "suspicious") for u in USER_POOL] * 2 +
        [(u, "fraud")      for u in USER_POOL[:4]] * 2  # only some users get fraud patterns
    )
    random.shuffle(patterns)
    patterns = patterns[:total]

    results = {"LEGITIMATE": 0, "SUSPICIOUS": 0, "FRAUD": 0, "error": 0}

    async with httpx.AsyncClient() as http:
        for i, (user, txn_type) in enumerate(patterns, 1):
            if txn_type == "legit":
                txn = make_legitimate_txn(user)
            elif txn_type == "suspicious":
                txn = make_suspicious_txn(user)
            else:
                txn = make_fraud_txn(user)

            print(f"  [{i:02d}/{total}] {txn_type.upper():12s} | {txn['transaction_id']} | "
                  f"{user['user_id']} | ${txn['amount']:>10,.2f} | "
                  f"{txn['location']['city']}, {txn['location']['country']}", end=" → ")

            result = await send_transaction(http, txn)
            if result:
                decision = result.get("decision", "?")
                score    = result.get("final_score", 0)
                print(f"{decision} ({score:.2f})")
                results[decision] = results.get(decision, 0) + 1
            else:
                print("ERROR")
                results["error"] += 1

            # Small delay so emails/alerts don't all fire at once
            await asyncio.sleep(0.5)

    print(f"\n{'─'*50}")
    print(f"  ✅ Simulation complete")
    print(f"  LEGITIMATE : {results.get('LEGITIMATE', 0)}")
    print(f"  SUSPICIOUS : {results.get('SUSPICIOUS', 0)}")
    print(f"  FRAUD      : {results.get('FRAUD', 0)}")
    print(f"  Errors     : {results.get('error', 0)}")
    print(f"\n  📬 View emails at: http://localhost:8025")
    print(f"  🖥  Admin dashboard: http://localhost:5173/dashboard")
    print(f"\n  User credentials (all share password '{PASSWORD}'):")
    for u in USER_POOL:
        print(f"    {u['email']}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fraud Detection Transaction Simulator")
    parser.add_argument("--users-only", action="store_true", help="Only seed users, no transactions")
    parser.add_argument("--count", type=int, default=30, help="Number of transactions to send")
    args = parser.parse_args()

    if args.users_only:
        asyncio.run(seed_users())
    else:
        asyncio.run(run_simulation(total=args.count))