from fastapi import APIRouter, HTTPException
from api.schemas.auth_schema import LoginRequest
from api.services.auth_service import login_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login")
async def login(credentials: LoginRequest):

    token = await login_user(credentials.email, credentials.password)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": token,
        "token_type": "bearer"
    }