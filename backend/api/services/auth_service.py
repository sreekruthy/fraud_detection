from database import mongo
from api.core.security import verify_password, create_access_token, hash_password
from api.utils.logger import log_login_success, log_login_failed
import uuid

# -----------------------------
# Login User
# -----------------------------
async def login_user(email: str, password: str):
    user = await mongo.db.users.find_one({"email": email})
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
    must_change = user.get("must_change_password", False)
    return {"token": token, "must_change_password": must_change}

# -----------------------------
# Register User
# -----------------------------
async def register_user(name: str, email: str, password: str, role: str):
    existing_user = await mongo.db.users.find_one({"email": email})
    if existing_user:
        return None
    new_user = {
        "user_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": role,
        "must_change_password": False
    }
    await mongo.db.users.insert_one(new_user)
    token = create_access_token(
        {"user_id": new_user["user_id"], "role": new_user["role"]}
    )
    return {"token": token, "must_change_password": False}

# -----------------------------
# Admin Create User with Temp Password
# -----------------------------
async def admin_create_user(name: str, email: str, temp_password: str, role: str):
    existing_user = await mongo.db.users.find_one({"email": email})
    if existing_user:
        return None
    new_user = {
        "user_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": hash_password(temp_password),
        "role": role,
        "must_change_password": True
    }
    await mongo.db.users.insert_one(new_user)
    return new_user

# -----------------------------
# Change Password
# -----------------------------
async def change_password(user_id: str, old_password: str, new_password: str):
    user = await mongo.db.users.find_one({"user_id": user_id})
    if not user:
        return None
    if not verify_password(old_password, user["password"]):
        return False
    await mongo.db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "password": hash_password(new_password),
            "must_change_password": False
        }}
    )
    return True