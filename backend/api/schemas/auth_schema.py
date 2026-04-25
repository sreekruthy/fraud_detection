from pydantic import BaseModel, EmailStr, validator
import re

def _validate_password_policy(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(value) > 20:
        raise ValueError("Password must not exceed 20 characters")
    if not any(c.isupper() for c in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[^\w\s]", value):
        raise ValueError("Password must contain at least one special character")
    if " " in value:
        raise ValueError("Password must not contain spaces")
    return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, v):
        return _validate_password_policy(v)

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "analyst"

    @validator("password")
    def password_strength(cls, v):
        return _validate_password_policy(v)

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    temp_password: str
    role: str = "analyst"

    @validator("temp_password")
    def password_strength(cls, v):
        return _validate_password_policy(v)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False