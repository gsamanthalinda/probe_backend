from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import JWTError, jwt

from probe.repositories.user import user_repository
from probe.schemas.user import UserCreate, UserUpdate, ForgotPasswordRequest, ResetPasswordConfirm
from probe.services.auth import hash_password, verify_password, create_access_token, create_refresh_token, revoke_user_tokens, revoke_user_tokens_by_id, refresh_access_token, verify_mfa_code, generate_mfa_secret, get_totp_uri, enable_mfa, disable_mfa, generate_backup_codes, hash_backup_code, is_locked_out, record_login_attempt, clear_login_attempts, get_user_id_from_refresh_token
from probe.services.email_service import send_password_reset_email


def authenticate_user(db: Session, email: str, password: str, code: Optional[str] = None):
    clean_email = email.strip().lower()

    if not clean_email or not password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required."
        )

    if is_locked_out(clean_email):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to too many failed attempts. Please try again later."
        )

    user = user_repository.get_by_email(db, clean_email)
    if not user or not verify_password(password, user.password_hash):
        record_login_attempt(clean_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if user.mfa_enabled:
        if not code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA code required",
                headers={"X-2FA-Required": "true"},
            )
        
        if not verify_mfa_code(user.mfa_secret, code):
            if user.mfa_backup_codes and code in user.mfa_backup_codes.split(","):
                pass
            else:
                record_login_attempt(clean_email)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code."
                )

    clear_login_attempts(clean_email)
    access_token = create_access_token(user.user_id, user.user_type)
    refresh_token = create_refresh_token(user.user_id, user.token_version or 1)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def get_user(db: Session, user_id: UUID, current_user):
    if str(current_user.user_id) != str(user_id) and current_user.user_type != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own account")
    db_user = user_repository.get_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User record not found")
    return db_user


def create_user(db: Session, data: UserCreate, current_user=None):
    clean_email = data.email.strip().lower()

    if not clean_email or not data.password_hash.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required authentication credentials cannot be empty."
        )

    if len(data.password_hash) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security policy violation: Password must be at least 8 characters long."
        )

    if len(clean_email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address exceeds maximum length."
        )

    clean_user_type = data.user_type.value.strip() if hasattr(data.user_type, 'value') else str(data.user_type).strip()
    if clean_user_type not in ["ADMIN", "RECYCLER", "UPS_COMPANY"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid system operational role requested."
        )

    if current_user and current_user.user_type != "ADMIN" and clean_user_type == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create ADMIN accounts."
        )

    existing_user = user_repository.get_by_email(db, clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user profile with this email address is already registered."
        )

    user_dict = data.model_dump()
    user_dict["email"] = clean_email
    user_dict["user_type"] = clean_user_type
    user_dict["password_hash"] = hash_password(user_dict["password_hash"])

    return user_repository.create(db, user_dict)


def update_user(db: Session, user_id: UUID, data: UserUpdate, current_user):
    if current_user.user_type != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update user details."
        )

    db_user = user_repository.get_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User record not found")

    update_data = data.model_dump(exclude_unset=True)

    if "password_hash" in update_data and update_data["password_hash"]:
        if len(update_data["password_hash"]) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security policy violation: Password must be at least 8 characters long."
            )
        update_data["password_hash"] = hash_password(update_data["password_hash"])

    if "email" in update_data:
        clean_email = update_data["email"].strip().lower()
        if len(clean_email) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address exceeds maximum length."
            )
        existing = user_repository.get_by_email(db, clean_email)
        if existing and str(existing.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user profile with this email address is already registered."
            )
        update_data["email"] = clean_email

    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID, current_user):
    if str(current_user.user_id) != str(user_id) and current_user.user_type != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own account")

    db_user = user_repository.get_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User record not found")

    user_repository.delete(db, db_user)


def list_users(db: Session, current_user):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN can list all users")
    return user_repository.get_all(db)


def request_password_reset(db: Session, data: ForgotPasswordRequest):
    clean_email = data.email.strip().lower()
    if not clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required."
        )

    user = user_repository.get_by_email(db, clean_email)
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        user_repository.update(db, user, {
            "reset_token": token,
            "reset_token_expires_at": expires_at
        })

        try:
            send_password_reset_email(user.email, token)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send password reset email: {e}")

    return {"message": "If an account exists with this email, a password reset link has been sent."}


def reset_password_with_token(db: Session, data: ResetPasswordConfirm):
    if not data.token or not data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required."
        )

    user = user_repository.get_by_reset_token(db, data.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    if user.reset_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired."
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security policy violation: Password must be at least 8 characters long."
        )

    hashed_password = hash_password(data.new_password)
    user_repository.update(db, user, {
        "password_hash": hashed_password,
        "reset_token": None,
        "reset_token_expires_at": None
    })

    return {"message": "Password reset successful."}


def logout_user(user_id: uuid.UUID):
    revoke_user_tokens_by_id(user_id)
    return {"message": "Logged out successfully."}


def refresh_token(db: Session, refresh_token: str):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required."
        )
    new_access_token = refresh_access_token(db, refresh_token)
    return {"access_token": new_access_token}


def setup_mfa(db: Session, user_id: uuid.UUID):
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled")
    
    secret = generate_mfa_secret()
    qr_uri = get_totp_uri(secret, user.email)
    plain_codes, hashed_codes = generate_backup_codes()
    
    user.mfa_secret = secret
    user.mfa_backup_codes = ",".join(hashed_codes)
    db.commit()
    db.refresh(user)
    
    return {
        "secret": secret,
        "qr_code_uri": qr_uri,
        "backup_codes": plain_codes,
    }


def verify_and_enable_mfa(db: Session, user_id: uuid.UUID, code: str):
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    secret = user.mfa_secret
    if not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA setup not initiated")
    
    if not verify_mfa_code(secret, code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")
    
    user.mfa_enabled = True
    db.commit()
    db.refresh(user)
    
    return {"message": "MFA enabled successfully"}


def disable_mfa_user(db: Session, user_id: uuid.UUID, password: str, code: str):
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    if not verify_mfa_code(user.mfa_secret, code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")
    
    user_repository.disable_mfa(db, user)
    return {"message": "MFA disabled successfully"}