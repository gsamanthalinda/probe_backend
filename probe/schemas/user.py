from datetime import datetime
from uuid import UUID
from .enums import UserType

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    user_type: UserType
    company_name: str

class UserCreate(UserBase):
    password_hash: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    user_type: Optional[UserType] = None
    company_name: Optional[str] = None

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)