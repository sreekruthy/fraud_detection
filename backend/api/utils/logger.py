import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/security.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("fraud_detection")

# ----------------------------
# Security Event Loggers
# ----------------------------
def log_login_success(email: str):
    logger.info(f"LOGIN SUCCESS | user: {email} | time: {datetime.utcnow()}")

def log_login_failed(email: str):
    logger.warning(f"LOGIN FAILED | user: {email} | time: {datetime.utcnow()}")

def log_unauthorized_access(endpoint: str):
    logger.warning(f"UNAUTHORIZED ACCESS | endpoint: {endpoint} | time: {datetime.utcnow()}")

def log_transaction(transaction_id: str, user_id: str):
    logger.info(f"TRANSACTION | id: {transaction_id} | user: {user_id} | time: {datetime.utcnow()}")

def log_fraud_flag(transaction_id: str, score: float):
    logger.warning(f"FRAUD FLAGGED | transaction: {transaction_id} | score: {score} | time: {datetime.utcnow()}")
