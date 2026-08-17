from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from probe.schemas.user import UserCreate, UserRead, UserUpdate, ForgotPasswordRequest, ResetPasswordConfirm
from probe.services.user import (
    get_user,
    create_user,
    update_user,
    delete_user,
    authenticate_user,
    list_users,
    request_password_reset,
    reset_password_with_token,
)
from probe.services.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def route_create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user(db, data)


@router.post("/login")
def route_login(email: str, password: str, db: Session = Depends(get_db)):
    return authenticate_user(db, email, password)


@router.post("/forgot-password")
def route_forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return request_password_reset(db, data)


@router.post("/reset-password")
def route_reset_password(
    data: ResetPasswordConfirm,
    db: Session = Depends(get_db),
):
    return reset_password_with_token(db, data)


@router.get("/", response_model=list[UserRead])
def route_list_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    return list_users(db, current_user)


@router.get("/{user_id}", response_model=UserRead)
def route_get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_user(db, user_id, current_user)


@router.patch("/{user_id}", response_model=UserRead)
def route_update_user(
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_user(db, user_id, data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def route_delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    delete_user(db, user_id, current_user)
