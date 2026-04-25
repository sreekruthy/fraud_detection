from fastapi import APIRouter, HTTPException, Depends
from api.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse, CreateUserRequest, ChangePasswordRequest
from api.services.auth_service import login_user, register_user, admin_create_user, change_password
from api.core.dependencies import get_current_user, require_role
from api.utils.logger import log_unauthorized_access

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# -----------------------------
# Login
# -----------------------------
@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    result = await login_user(credentials.email, credentials.password)
    if not result:
        log_unauthorized_access("/api/auth/login")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": result["token"],
        "token_type": "bearer",
        "must_change_password": result["must_change_password"]
    }

# -----------------------------
# Register
# -----------------------------
@router.post("/register", response_model=TokenResponse)
async def register(user_data: RegisterRequest):
    result = await register_user(
        user_data.name,
        user_data.email,
        user_data.password,
        user_data.role
    )
    if not result:
        raise HTTPException(status_code=400, detail="User already exists")
    return {
        "access_token": result["token"],
        "token_type": "bearer",
        "must_change_password": result["must_change_password"]
    }

# -----------------------------
# Admin Create User
# -----------------------------
@router.post("/admin/create-user")
async def create_user(
    user_data: CreateUserRequest,
    current_user=Depends(require_role("admin"))
):
    result = await admin_create_user(
        user_data.name,
        user_data.email,
        user_data.temp_password,
        user_data.role
    )
    if not result:
        raise HTTPException(status_code=400, detail="User already exists")
    return {
        "message": f"User {user_data.email} created successfully",
        "must_change_password": True,
        "temp_password": user_data.temp_password
    }

# -----------------------------
# Change Password
# -----------------------------
@router.post("/change-password")
async def change_user_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_user)
):
    result = await change_password(
        current_user["user_id"],
        data.old_password,
        data.new_password
    )
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    return {"message": "Password changed successfully"}