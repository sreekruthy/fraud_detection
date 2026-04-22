from fastapi import APIRouter, Query
from database.mongo import db

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


def _serialize(txn: dict) -> dict:
    for f in ("timestamp", "created_at", "feedback_received_at", "hold_expires_at"):
        if f in txn and hasattr(txn[f], "isoformat"):
            txn[f] = txn[f].isoformat()
    return txn


@router.get("/flagged")
async def fetch_flagged(status: str | None = Query(None)):
    """SUSPICIOUS + FRAUD transactions. Filter by ?status=ON_HOLD etc."""
    query: dict = {"decision": {"$in": ["SUSPICIOUS", "FRAUD"]}}
    if status:
        query["txn_status"] = status

    txns = []
    async for t in db.transactions.find(query, {"_id": 0}).sort("created_at", -1).limit(100):
        txns.append(_serialize(t))
    return {"transactions": txns}


@router.get("/user/{user_id}")
async def fetch_user_transactions(user_id: str):
    txns = []
    async for t in db.transactions.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(50):
        txns.append(_serialize(t))
    return {"transactions": txns, "total": len(txns)}


@router.get("/{transaction_id}")
async def fetch_transaction(transaction_id: str):
    txn = await db.transactions.find_one({"transaction_id": transaction_id}, {"_id": 0})
    if not txn:
        return {"transaction": None}
    return {"transaction": _serialize(txn)}