from pydantic import BaseModel, EmailStr


class AdminModel(BaseModel):

    admin_id: str
    name: str
    email: EmailStr
    password: str
    role: str = "admin"
