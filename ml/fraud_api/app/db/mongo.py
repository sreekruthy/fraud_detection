"""
app/db/mongo.py
----------------
Provides a ready-to-use `db` object at import time.
No startup lifecycle call needed — just `from app.db.mongo import db`.

Env vars (from ml/fraud_api/.env):
    MONGO_URI     — full MongoDB connection string  (e.g. mongodb+srv://...)
    DB_NAME       — database name                  (e.g. FraudDetection)

Falls back to MONGO_URL / DATABASE_NAME for compatibility with older .env files.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# ── Load .env ─────────────────────────────────────────────────────────────────
# Walk up to ml/fraud_api/.env from wherever this file lives
_here    = Path(__file__).resolve()                  # app/db/mongo.py
_env     = _here.parent.parent / ".env"              # ml/fraud_api/.env
load_dotenv(dotenv_path=_env)

# ── Read env vars — support both naming conventions ───────────────────────────
MONGO_URI     = os.getenv("MONGO_URI") or os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DB_NAME")  or os.getenv("DATABASE_NAME", "FraudDetection")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI not found in environment.\n"
        f"Expected it in: {_env}\n"
        "Add:  MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/"
    )

# ── Create client and db — available immediately at import time ───────────────
_client = AsyncIOMotorClient(MONGO_URI)
db      = _client[DATABASE_NAME]

print(f"✅ MongoDB ready (db='{DATABASE_NAME}')")