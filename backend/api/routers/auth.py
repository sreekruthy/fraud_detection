from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import mongo
from passlib.context import CryptContext

router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------- REQUEST MODEL ----------------
class User(BaseModel):
    email: str
    password: str


# ---------------- LOGIN API ----------------
@router.post("/login")
async def login(user: User):
    print("\n===== LOGIN DEBUG =====")
    print("INPUT EMAIL:", user.email)

    # Find user in admins collection
    db_user = await mongo.db.admins.find_one({"email": user.email})

    if not db_user:
        print("❌ USER NOT FOUND")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_hash = db_user.get("password_hash")

    if not stored_hash:
        print("❌ PASSWORD HASH MISSING IN DB")
        raise HTTPException(status_code=500, detail="Server error")

    try:
        match = pwd_context.verify(user.password, stored_hash)
        print("PASSWORD MATCH:", match)
    except Exception as e:
        print("❌ HASH VERIFY ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Hash error")

    if not match:
        print("❌ WRONG PASSWORD")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print("✅ LOGIN SUCCESS")
    print("========================\n")

    return {
        "message": "Login successful",
        "email": db_user["email"],
        "role": db_user.get("role", "admin")
    }