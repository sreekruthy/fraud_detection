from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env file from parent directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = None
db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    print("✅ MongoDB Connected")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")

if MONGO_URL:
    print("MONGO_URL: configured")
else:
    print("MONGO_URL: missing")
print("DB:", DATABASE_NAME)
