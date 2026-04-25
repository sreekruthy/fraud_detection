from fastapi import APIRouter, HTTPException
from api.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse
from api.services.auth_service import login_user, register_user
from api.utils.logger import log_unauthorized_access

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# -----------------------------
# Login
# -----------------------------
@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    token = await login_user(credentials.email, credentials.password)
    if not token:
        log_unauthorized_access("/api/auth/login")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": token,
        "token_type": "bearer"
    }

# -----------------------------
# Register
# -----------------------------
@router.post("/register", response_model=TokenResponse)
async def register(user_data: RegisterRequest):
    token = await register_user(
        user_data.name,
        user_data.email,
        user_data.password,
        user_data.role
    )
    if not token:
        raise HTTPException(status_code=400, detail="User already exists")
    return {
        "access_token": token,
        "token_type": "bearer"
    }