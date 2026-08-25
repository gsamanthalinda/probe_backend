from datetime import datetime
from uuid import UUID
from .enums import UserType

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr = Field(..., max_length=255)
    user_type: UserType
    company_name: str = Field(..., max_length=255)

class UserCreate(UserBase):
    password_hash: str = Field(..., min_length=8, max_length=72)


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=255)
    password_hash: Optional[str] = Field(None, min_length=8, max_length=72)
    user_type: Optional[UserType] = None
    company_name: Optional[str] = Field(None, max_length=255)

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    created_at: datetime
    mfa_enabled: bool = False


class UserRegisterResponse(BaseModel):
    user: UserRead


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_uri: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class MFADisableRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=72)
    code: str = Field(..., min_length=6, max_length=6)


class MFALoginRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=72)
    code: Optional[str] = Field(None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)


class ResetPasswordConfirm(BaseModel):
    token: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=72)