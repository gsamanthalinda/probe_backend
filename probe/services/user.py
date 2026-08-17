from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
import secrets
from datetime import datetime, timezone, timedelta

from probe.repositories.user import user_repository
from probe.schemas.user import UserCreate, UserUpdate, ForgotPasswordRequest, ResetPasswordConfirm
from probe.services.auth import hash_password, verify_password, create_access_token
from probe.services.email_service import send_password_reset_email


def authenticate_user(db: Session, email: str, password: str):
    clean_email = email.strip().lower()
    user = user_repository.get_by_email(db, clean_email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    token = create_access_token(user.user_id, user.user_type)
    return {"access_token": token, "token_type": "bearer"}


def get_user(db: Session, user_id: UUID, current_user):
    if str(current_user.user_id) != str(user_id) and current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="You can only view your own account")
    db_user = user_repository.get_by_id(db, str(user_id))
    if not db_user:
        raise HTTPException(status_code=404, detail="User record not found")
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

    db_user = user_repository.get_by_id(db, str(user_id))
    if not db_user:
        raise HTTPException(status_code=404, detail="User record not found")

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
        raise HTTPException(status_code=403, detail="You can only delete your own account")

    db_user = user_repository.get_by_id(db, str(user_id))
    if not db_user:
        raise HTTPException(status_code=404, detail="User record not found")

    user_repository.delete(db, db_user)


def list_users(db: Session, current_user):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Only ADMIN can list all users")
    return user_repository.get_all(db)


def request_password_reset(db: Session, data: ForgotPasswordRequest):
    clean_email = data.email.strip().lower()
    user = user_repository.get_by_email(db, clean_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    user_repository.update(db, user, {
        "reset_token": token,
        "reset_token_expires_at": expires_at
    })

    send_password_reset_email(user.email, token)

    return {"message": "Password reset link sent to your email."}


def reset_password_with_token(db: Session, data: ResetPasswordConfirm):
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

    hashed_password = hash_password(data.new_password)
    user_repository.update(db, user, {
        "password_hash": hashed_password,
        "reset_token": None,
        "reset_token_expires_at": None
    })

    return {"message": "Password reset successful."}