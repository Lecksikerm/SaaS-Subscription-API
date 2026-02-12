from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_verified: Optional[bool] = None  # Added this

class UserInDB(UserBase):
    id: uuid.UUID
    subscription_tier: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
