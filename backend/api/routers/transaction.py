from fastapi import APIRouter, Depends, Query
from api.schemas.transaction_schema import TransactionCreate
from api.services.transaction_service import create_transaction, get_transaction
from api.core.dependencies import get_current_user
from api.utils.logger import log_transaction
from database import mongo

router = APIRouter(tags=["Transactions"])


def _serialize(txn: dict) -> dict:
    for f in ("timestamp", "created_at", "feedback_received_at", "hold_expires_at"):
        if f in txn and hasattr(txn[f], "isoformat"):
            txn[f] = txn[f].isoformat()
    return txn


# -------------------------
# POST Transaction (Protected)
# -------------------------
@router.post("/")
async def ingest_transaction(
    transaction: TransactionCreate,
    current_user=Depends(get_current_user)
):
    transaction_data = transaction.dict()
    result = await create_transaction(transaction_data)
    log_transaction(result["transaction_id"], current_user["user_id"])
    return {
        "message": "Transaction stored successfully",
        "data": result
    }


# -------------------------
# GET Flagged Transactions
# -------------------------
@router.get("/flagged")
async def fetch_flagged(status: str | None = Query(None)):
    """SUSPICIOUS + FRAUD transactions. Filter by ?status=ON_HOLD etc."""
    query: dict = {"decision": {"$in": ["SUSPICIOUS", "FRAUD"]}}
    if status:
        query["txn_status"] = status

    txns = []
    async for t in mongo.db.transactions.find(query, {"_id": 0}).sort("created_at", -1).limit(100):
        txns.append(_serialize(t))
    return {"transactions": txns}


# -------------------------
# GET User Transactions
# -------------------------
@router.get("/user/{user_id}")
async def fetch_user_transactions(user_id: str):
    txns = []
    async for t in mongo.db.transactions.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(50):
        txns.append(_serialize(t))
    return {"transactions": txns, "total": len(txns)}


# -------------------------
# GET Transaction (Protected)
# -------------------------
@router.get("/{transaction_id}")
async def fetch_transaction(
    transaction_id: str,
    current_user=Depends(get_current_user)
):
    transaction = await get_transaction(transaction_id)
    return {
        "transaction": transaction
    }
