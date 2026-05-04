from database import mongo
from api.core.security import verify_password, create_access_token, hash_password
from api.utils.logger import log_login_success, log_login_failed
import uuid
from datetime import datetime


# Admin Login
async def login_user(email: str, password: str):
    # Look up in admins collection (not users)
    admin = await mongo.db.admins.find_one({"email": email})
    if not admin:
        log_login_failed(email)
        return None

    # Compare against password_hash field
    if not verify_password(password, admin["password_hash"]):
        log_login_failed(email)
        return None

    log_login_success(email)
    token = create_access_token(
        {"user_id": admin["admin_id"], "role": admin["role"]}
    )
    return token



# Admin Creation (called only by a SuperAdmin or script)
async def register_user(name: str, email: str, password: str, role: str):
    # Prevent duplicate admin accounts
    existing = await mongo.db.admins.find_one({"email": email})
    if existing:
        return None

    new_admin = {
        "admin_id": "ADM" + str(uuid.uuid4())[:5].upper(),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),   # always hash, never plain text
        "role": role,
        "created_at": datetime.utcnow().isoformat(),
        "must_change_password": True                 # force password change on first login
    }

    await mongo.db.admins.insert_one(new_admin)

    token = create_access_token(
        {"user_id": new_admin["admin_id"], "role": new_admin["role"]}
    )
    return token