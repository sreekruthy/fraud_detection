from motor.motor_asyncio import AsyncIOMotorClient
from api.core.config import settings


# Create MongoDB client
client = AsyncIOMotorClient(settings.MONGO_URL)

# Access the database
db = client[settings.DATABASE_NAME]


# Optional: startup connection check
async def connect_to_mongo():
    try:
        await client.admin.command("ping")
        print("MongoDB connection successful")
    except Exception as e:
        print("MongoDB connection failed:", e)


# Optional: close connection
async def close_mongo_connection():
    client.close()
