from pydantic import BaseModel, EmailStr


class UserModel(BaseModel):

    user_id: str
    name: str
    email: EmailStr
    password: str
    role: str
