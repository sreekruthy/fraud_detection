from database import mongo
from datetime import datetime

async def create_transaction(transaction_data: dict):
    transaction_data["created_at"] = datetime.utcnow()
    result = await mongo.db.transactions.insert_one(transaction_data)
    return transaction_data

async def get_transaction(transaction_id: str):
    transaction = await mongo.db.transactions.find_one(
        {"transaction_id": transaction_id},
        {"_id": 0}
    )
    return transaction