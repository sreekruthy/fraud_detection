from fastapi import APIRouter
from api.schemas.transaction_schema import TransactionCreate
from api.services.transaction_service import create_transaction, get_transaction

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


# -------------------------
# POST Transaction
# -------------------------
@router.post("/")
async def ingest_transaction(transaction: TransactionCreate):

    transaction_data = transaction.dict()

    result = await create_transaction(transaction_data)

    return {
        "message": "Transaction stored successfully",
        "data": result
    }


# -------------------------
# GET Transaction
# -------------------------
@router.get("/{transaction_id}")
async def fetch_transaction(transaction_id: str):

    transaction = await get_transaction(transaction_id)

    return {
        "transaction": transaction
    }