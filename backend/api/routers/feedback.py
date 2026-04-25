"""
api/routers/feedback.py
------------------------
Handles user responses from email verification links.

SUSPICIOUS responses:
  - User responded in time → update txn_status, resolve alert
  - "legitimate" → CONFIRMED_LEGIT (transaction processed)
  - "fraud"      → BLOCKED (transaction blocked)
  - Either way, the alert is resolved and admin is no longer needed

FRAUD responses:
  - Transaction is already BLOCKED — response does NOT change txn_status
  - Response is saved to customer_feedback for retraining ONLY
  - "legitimate" → user is reminded to redo the transaction
  - "fraud"      → thank user, account flagged for review
  - Alert stays as AUTO_BLOCKED (already resolved)

Admin action endpoint:
  - Used for SUSPICIOUS transactions ONLY (after user window expires)
  - Admin sees user history summary and makes PERMIT or BLOCK decision
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timezone
import jwt
import os

from database import mongo
from api.services.alert_service import resolve_alert

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

FEEDBACK_SECRET = os.getenv("FEEDBACK_JWT_SECRET", "feedbacksecretkey")


class AnalystFeedback(BaseModel):
    transaction_id:   str
    analyst_decision: str    # LEGITIMATE | FRAUD
    comments:         str | None = None


class AdminAction(BaseModel):
    transaction_id: str
    action:         str   # BLOCK | PERMIT


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, FEEDBACK_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="This verification link has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid verification link.")


# ── GET /verify — frontend calls this to show transaction info ────────────────

@router.get("/verify")
async def get_verify_info(token: str = Query(...)):
    txn = await mongo.db.transactions.find_one({"transaction_id": txn_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    # Serialize datetime
    for f in ("timestamp", "created_at", "hold_expires_at", "feedback_received_at"):
        if f in txn and hasattr(txn[f], "isoformat"):
            txn[f] = txn[f].isoformat()

    if txn.get("customer_feedback") is not None:
        return {
            "already_responded": True,
            "feedback":          txn["customer_feedback"],
            "transaction_id":    txn_id,
            "decision":          txn.get("decision"),
        }

    return {
        "already_responded": False,
        "transaction_id":    txn["transaction_id"],
        "amount":            txn["amount"],
        "decision":          txn["decision"],
        "txn_status":        txn.get("txn_status"),
        "location":          txn.get("location"),
        "timestamp":         txn.get("timestamp"),
        "explainability":    txn.get("explainability", {}),
        "final_score":       txn.get("final_score", 0),
        "hold_expires_at":   txn.get("hold_expires_at"),
        "purpose":           purpose,   # "suspicious_verify" or "fraud_feedback"
    }


# ── POST /respond — user clicks email button ──────────────────────────────────

@router.post("/respond")
async def user_respond(
    token:    str = Query(...),
    response: str = Query(...),
):
    if response not in ("legitimate", "fraud"):
        raise HTTPException(status_code=400, detail="Response must be 'legitimate' or 'fraud'.")

    txn = await mongo.db.transactions.find_one({"transaction_id": txn_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    # Prevent double response
    if txn.get("customer_feedback") is not None:
        return {
            "already_responded": True,
            "feedback":          txn["customer_feedback"],
            "txn_status":        txn.get("txn_status"),
            "transaction_id":    txn_id,
        }

    now = datetime.now(timezone.utc)

    # ── SUSPICIOUS response ───────────────────────────────────────────────────
    # User responded → their answer determines txn_status
    if purpose == "suspicious_verify" or txn.get("decision") == "SUSPICIOUS":
        new_status   = "CONFIRMED_LEGIT" if response == "legitimate" else "BLOCKED"
        admin_action = "PERMIT_USER_CONFIRMED" if response == "legitimate" else "BLOCK_USER_CONFIRMED"

        await mongo.db.transactions.update_one(
            {"transaction_id": txn_id},
            {"$set": {
                "customer_feedback":    response,
                "feedback_received_at": now,
                "txn_status":           new_status,
            }}
        )
        await resolve_alert(txn_id, admin_action)

        return {
            "already_responded": False,
            "decision":          txn["decision"],
            "feedback":          response,
            "txn_status":        new_status,
            "transaction_id":    txn_id,
            "message": (
                "Your transaction has been confirmed and will be processed."
                if response == "legitimate"
                else "Your transaction has been blocked. Your account is being reviewed."
            ),
        }

    # ── FRAUD response ────────────────────────────────────────────────────────
    # Transaction is already BLOCKED. Response is for retraining only.
    # txn_status does NOT change.
    elif purpose == "fraud_feedback" or txn.get("decision") == "FRAUD":
        await mongo.db.transactions.update_one(
            {"transaction_id": txn_id},
            {"$set": {
                "customer_feedback":    response,
                "feedback_received_at": now,
                # txn_status stays BLOCKED — response is informational only
            }}
        )

        return {
            "already_responded": False,
            "decision":          "FRAUD",
            "feedback":          response,
            "txn_status":        "BLOCKED",   # unchanged
            "transaction_id":    txn_id,
            "message": (
                "Thank you for confirming. This transaction has been blocked. "
                "Please redo your transaction — this one cannot be reversed."
                if response == "legitimate"
                else
                "Thank you for reporting this. Your account has been flagged for review. "
                "No further action is needed from you."
            ),
        }

    # Fallback
    return {"message": "Response recorded.", "transaction_id": txn_id}


# ── POST /admin-action — admin PERMIT or BLOCK (SUSPICIOUS only) ──────────────

@router.post("/admin-action")
async def admin_action(action_data: AdminAction):
    """
    Admin manually decides on a SUSPICIOUS transaction.
    Called when:
      - Admin proactively acts from dashboard
      - OR the 2-minute user window has expired and user didn't respond
    NOT used for FRAUD — those are auto-blocked.
    """
    txn = await mongo.db.transactions.find_one({"transaction_id": action_data.transaction_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    if txn.get("decision") == "FRAUD":
        raise HTTPException(
            status_code=400,
            detail="Fraud transactions are auto-blocked. Admin action not applicable."
        )

    new_status   = "BLOCKED" if action_data.action == "BLOCK" else "CONFIRMED_LEGIT"
    admin_action = f"ADMIN_{action_data.action}"

    await mongo.db.transactions.update_one(
        {"transaction_id": action_data.transaction_id},
        {"$set": {
            "txn_status":           new_status,
            "feedback_received_at": datetime.now(timezone.utc),
            "customer_feedback":    f"admin:{action_data.action}",
        }}
    )
    await resolve_alert(action_data.transaction_id, admin_action)

    return {
        "message":        f"Transaction {action_data.action}ED by admin.",
        "txn_status":     new_status,
        "transaction_id": action_data.transaction_id,
    }


# ── POST /analyst — analyst manual review ────────────────────────────────────

    txn = await mongo.db.transactions.find_one({"transaction_id": feedback.transaction_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    new_status = (
        "CONFIRMED_LEGIT" if feedback.analyst_decision == "LEGITIMATE" else "BLOCKED"
    )
    update = {
        "customer_feedback":    f"analyst:{feedback.analyst_decision}",
        "feedback_received_at": datetime.now(timezone.utc),
        "txn_status":           new_status,
    }
    if feedback.comments:
        update["analyst_comments"] = feedback.comments

    await mongo.db.transactions.update_one(
        {"transaction_id": feedback.transaction_id},
        {"$set": update}
    )
    admin_action = "PERMIT_ANALYST" if feedback.analyst_decision == "LEGITIMATE" else "BLOCK_ANALYST"
    await resolve_alert(feedback.transaction_id, admin_action)

    return {
        "message":        f"Marked as {feedback.analyst_decision} by analyst.",
        "txn_status":     new_status,
        "transaction_id": feedback.transaction_id,
    }