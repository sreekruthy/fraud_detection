"""
transaction_simulator.py
------------------------
Place this file at your PROJECT ROOT:
  fraud_detection/transaction_simulator.py

Run from project root:
  python transaction_simulator.py --users-only
  python transaction_simulator.py --count 30

This script:
  1. Reads MongoDB URI from ml/fraud_api/.env (where your MONGO_URI lives)
  2. Seeds 8 test users into the users collection
  3. Sends transactions to the ML API at port 8000
"""

import asyncio
import argparse
import random
import uuid
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Load .env from ml/fraud_api/.env (that's where MONGO_URI lives) ───────────
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent          # project root
ML_ENV   = BASE_DIR / "ml" / "fraud_api" / ".env"

if ML_ENV.exists():
    load_dotenv(ML_ENV)
    print(f"✅ Loaded env from {ML_ENV}")
else:
    load_dotenv(BASE_DIR / ".env")
    print(f"⚠️  ml/fraud_api/.env not found, trying project root .env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "FraudDetection")
ML_API    = "http://localhost:8000/transaction"
PASSWORD  = "test1234"

if not MONGO_URI:
    print("\n❌ ERROR: MONGO_URI not found in environment.")
    print("   Make sure ml/fraud_api/.env contains:")
    print("   MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/")
    sys.exit(1)

print(f"✅ MONGO_URI loaded (DB: {DB_NAME})")

# ── Import motor AFTER confirming env loaded ──────────────────────────────────
import httpx
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]

# ── User pool ─────────────────────────────────────────────────────────────────
USER_POOL = [
    {"user_id": "USR_001", "name": "Alice Johnson", "email": "alice@mailhog.test",  "home_city": "New York"},
    {"user_id": "USR_002", "name": "Bob Smith",     "email": "bob@mailhog.test",    "home_city": "Los Angeles"},
    {"user_id": "USR_003", "name": "Carol White",   "email": "carol@mailhog.test",  "home_city": "Chicago"},
    {"user_id": "USR_004", "name": "David Lee",     "email": "david@mailhog.test",  "home_city": "Houston"},
    {"user_id": "USR_005", "name": "Eva Martinez",  "email": "eva@mailhog.test",    "home_city": "Phoenix"},
    {"user_id": "USR_006", "name": "Frank Kim",     "email": "frank@mailhog.test",  "home_city": "San Jose"},
    {"user_id": "USR_007", "name": "Grace Patel",   "email": "grace@mailhog.test",  "home_city": "Dallas"},
    {"user_id": "USR_008", "name": "Henry Brown",   "email": "henry@mailhog.test",  "home_city": "Philadelphia"},
]

# ── Locations ─────────────────────────────────────────────────────────────────
NORMAL_LOCATIONS = [
    {"city": "New York",     "country": "US", "latitude": 40.7128,  "longitude": -74.0060},
    {"city": "Los Angeles",  "country": "US", "latitude": 34.0522,  "longitude": -118.2437},
    {"city": "Chicago",      "country": "US", "latitude": 41.8781,  "longitude": -87.6298},
    {"city": "Houston",      "country": "US", "latitude": 29.7604,  "longitude": -95.3698},
    {"city": "Phoenix",      "country": "US", "latitude": 33.4484,  "longitude": -112.0740},
    {"city": "Dallas",       "country": "US", "latitude": 32.7767,  "longitude": -96.7970},
    {"city": "San Jose",     "country": "US", "latitude": 37.3382,  "longitude": -121.8863},
]

FRAUD_LOCATIONS = [
    {"city": "Lagos",     "country": "NG", "latitude": 6.5244,  "longitude": 3.3792},
    {"city": "Bucharest", "country": "RO", "latitude": 44.4268, "longitude": 26.1025},
    {"city": "Bangkok",   "country": "TH", "latitude": 13.7563, "longitude": 100.5018},
    {"city": "Minsk",     "country": "BY", "latitude": 53.9045, "longitude": 27.5615},
]

BROWSERS     = ["Chrome", "Firefox", "Safari", "Edge"]
RECEIVER_IDS = [f"RCV_{i:03d}" for i in range(1, 20)]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Seed users ────────────────────────────────────────────────────────────────

async def seed_users():
    print("\n👥 Seeding users into MongoDB…")
    created = 0
    for u in USER_POOL:
        existing = await db.users.find_one({"user_id": u["user_id"]})
        if existing:
            print(f"  ⏭  {u['user_id']} ({u['name']}) already exists — skipping")
            continue

        await db.users.insert_one({
            "user_id":                u["user_id"],
            "name":                   u["name"],
            "email":                  u["email"],
            "password":               hash_password(PASSWORD),
            "home_city":              u["home_city"],
            "account_created_at":     datetime.now(timezone.utc).isoformat(),
            "avg_transaction_amount": 0,
            "transaction_frequency":  0,
            "historical_risk_score":  0.0,
        })
        print(f"  ✅ Created {u['user_id']} | {u['name']} | {u['email']} | password: {PASSWORD}")
        created += 1

    print(f"\n  Done — {created} new users created, {len(USER_POOL) - created} already existed.\n")


# ── Build transaction payloads ─────────────────────────────────────────────────

def _txn_id():
    return f"TXN_{uuid.uuid4().hex[:10].upper()}"

def _device(user_id):
    return {
        "ip":        f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
        "device_id": f"DEV_{user_id}_{random.randint(1,5)}",
        "browser":   random.choice(BROWSERS),
    }

def make_legit_txn(user):
    """Low amount, US location, daytime hour → likely LEGITIMATE"""
    ts = datetime.now(timezone.utc).replace(hour=random.randint(9, 18))
    return {
        "transaction_id": _txn_id(),
        "user_id":        user["user_id"],
        "amount":         round(random.uniform(20, 1500), 2),
        "currency":       "USD",
        "timestamp":      ts.isoformat(),
        "location":       random.choice(NORMAL_LOCATIONS),
        "device":         _device(user["user_id"]),
        "receiver_id":    random.choice(RECEIVER_IDS),
        "user_home_city": user["home_city"],
    }

def make_suspicious_txn(user):
    """Higher amount, late hour → may trigger SUSPICIOUS"""
    ts = datetime.now(timezone.utc).replace(hour=random.choice([0, 1, 22, 23]))
    return {
        "transaction_id": _txn_id(),
        "user_id":        user["user_id"],
        "amount":         round(random.uniform(5000, 8000), 2),
        "currency":       "USD",
        "timestamp":      ts.isoformat(),
        "location":       random.choice(NORMAL_LOCATIONS),
        "device":         _device(user["user_id"]),
        "receiver_id":    random.choice(RECEIVER_IDS),
        "user_home_city": user["home_city"],
    }

def make_fraud_txn(user):
    """Very high amount + foreign country + unusual hour → likely FRAUD"""
    ts = datetime.now(timezone.utc).replace(hour=random.randint(2, 5))
    return {
        "transaction_id": _txn_id(),
        "user_id":        user["user_id"],
        "amount":         round(random.uniform(15000, 50000), 2),
        "currency":       "USD",
        "timestamp":      ts.isoformat(),
        "location":       random.choice(FRAUD_LOCATIONS),
        "device":         _device(user["user_id"]),
        "receiver_id":    random.choice(RECEIVER_IDS),
        "user_home_city": user["home_city"],
    }


# ── Send one transaction to ML API ────────────────────────────────────────────

async def send_txn(http: httpx.AsyncClient, txn: dict):
    try:
        res = await http.post(ML_API, json=txn, timeout=15.0)
        res.raise_for_status()
        return res.json()
    except httpx.ConnectError:
        print(f"\n❌ Cannot connect to ML API at {ML_API}")
        print("   Make sure you ran: cd ml/fraud_api && uvicorn main:app --reload --port 8000")
        return None
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None


# ── Main simulation ────────────────────────────────────────────────────────────

async def run_simulation(total: int = 30):
    await seed_users()

    print(f"🚀 Sending {total} transactions to {ML_API}…\n")
    print(f"   NOTE: First few transactions per user will have rule_score=0.0")
    print(f"   because there's no history yet. That's normal.\n")

    # Weighted pattern list — repeated users so history accumulates
    patterns = (
        [(u, "legit")      for u in USER_POOL] * 5 +
        [(u, "suspicious") for u in USER_POOL] * 2 +
        [(u, "fraud")      for u in USER_POOL[:4]] * 2
    )
    random.shuffle(patterns)
    patterns = patterns[:total]

    counts = {"LEGITIMATE": 0, "SUSPICIOUS": 0, "FRAUD": 0, "error": 0}

    async with httpx.AsyncClient() as http:
        for i, (user, ptype) in enumerate(patterns, 1):
            txn = (make_legit_txn if ptype == "legit" else
                   make_suspicious_txn if ptype == "suspicious" else
                   make_fraud_txn)(user)

            print(f"  [{i:02d}/{total}] {ptype.upper():12s} | {txn['transaction_id']} | "
                  f"{user['user_id']} | ${txn['amount']:>10,.2f} | "
                  f"{txn['location']['city']}, {txn['location']['country']}", end="  →  ")
            sys.stdout.flush()

            result = await send_txn(http, txn)
            if result:
                decision = result.get("decision", "?")
                score    = result.get("final_score", 0)
                status   = result.get("txn_status", "")
                print(f"{decision} ({score:.2f})  [{status}]")
                counts[decision] = counts.get(decision, 0) + 1
            else:
                print("ERROR")
                counts["error"] += 1
                if counts["error"] >= 3:
                    print("\n⛔ Too many errors in a row — aborting.")
                    break

            await asyncio.sleep(0.4)

    print(f"\n{'─'*55}")
    print(f"  Simulation complete")
    print(f"  LEGITIMATE : {counts.get('LEGITIMATE', 0)}")
    print(f"  SUSPICIOUS : {counts.get('SUSPICIOUS', 0)}")
    print(f"  FRAUD      : {counts.get('FRAUD', 0)}")
    print(f"  Errors     : {counts.get('error', 0)}")
    print(f"\n  📬 View emails at:    http://localhost:8025")
    print(f"  🖥  Admin dashboard:   http://localhost:5173/dashboard")
    print(f"\n  Test users (password: {PASSWORD}):")
    for u in USER_POOL:
        print(f"    {u['email']}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users-only", action="store_true", help="Only seed users, skip transactions")
    parser.add_argument("--count", type=int, default=30, help="Number of transactions to send")
    args = parser.parse_args()

    if args.users_only:
        asyncio.run(seed_users())
    else:
        asyncio.run(run_simulation(total=args.count))