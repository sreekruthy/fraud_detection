from database import mongo
from api.core.security import verify_password, create_access_token


# -----------------------------
# Login User
# -----------------------------
async def login_user(email: str, password: str):

    user = await mongo.db.users.find_one({"email": email})

    if not user:
        return None

    if not verify_password(password, user["password"]):
        return None

    token = create_access_token(
        {"user_id": user["user_id"], "role": user["role"]}
    )

    return token