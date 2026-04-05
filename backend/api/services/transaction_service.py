from database import mongo
from datetime import datetime


# -----------------------------
# Store Transaction
# -----------------------------
async def create_transaction(transaction_data: dict):

    transaction_data["created_at"] = datetime.utcnow()
    transaction_data["risk_score"] = None
    transaction_data["fraud_label"] = None

    result = await mongo.db.transactions.insert_one(transaction_data)

    return {
        "transaction_id": transaction_data["transaction_id"],
        "db_id": str(result.inserted_id)
    }


# -----------------------------
# Get Transaction
# -----------------------------
async def get_transaction(transaction_id: str):

    transaction = await mongo.db.transactions.find_one(
        {"transaction_id": transaction_id},
        {"_id": 0}
    )

    return transaction