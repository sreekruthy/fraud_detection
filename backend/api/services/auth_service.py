from database.db.mongo import db
from api.core.security import verify_password, create_access_token, hash_password
from api.utils.logger import log_login_success, log_login_failed
import uuid

# -----------------------------
# Login User
# -----------------------------
async def login_user(email: str, password: str):
    user = await db.users.find_one({"email": email})
    
    if not user:
        log_login_failed(email)
        return None
    
    if not verify_password(password, user["password"]):
        log_login_failed(email)
        return None
    
    log_login_success(email)
    
    token = create_access_token(
        {"user_id": user["user_id"], "role": user["role"]}
    )
    return token

# -----------------------------
# Register User
# -----------------------------
async def register_user(name: str, email: str, password: str, role: str):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        return None
    
    # Create new user
    new_user = {
        "user_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": role
    }
    
    await db.users.insert_one(new_user)
    
    token = create_access_token(
        {"user_id": new_user["user_id"], "role": new_user["role"]}
    )
    return token
