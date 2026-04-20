from fastapi import APIRouter, Depends
from api.schemas.transaction_schema import TransactionCreate
from api.services.transaction_service import create_transaction, get_transaction
from api.core.dependencies import get_current_user
from api.utils.logger import log_transaction, log_unauthorized_access

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

# -------------------------
# POST Transaction
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
# GET Transaction
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
