"""
app/db/mongo.py
---------------
Creates a single shared MongoDB client and exposes the database object.
Every other file imports `db` from here — one connection pool, shared everywhere.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "FraudDetection")

# Single client instance shared across the entire app
client = AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]