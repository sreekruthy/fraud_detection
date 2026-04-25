from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = None
db = None


# ---------------- CONNECT ----------------
async def connect_to_mongo():
    global client, db

    if not MONGO_URL:
        raise Exception("❌ MONGO_URL not found in .env")

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]

    print("✅ MongoDB Connected")
    print("DB:", DATABASE_NAME)


# ---------------- DISCONNECT ----------------
async def close_mongo_connection():
    global client

    if client:
        client.close()
        print("❌ MongoDB connection closed")