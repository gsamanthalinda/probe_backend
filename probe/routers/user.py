from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from probe.schemas.user import UserCreate, UserRead, UserRegisterResponse, UserUpdate, ForgotPasswordRequest, ResetPasswordConfirm
from probe.services.user import (
    get_user,
    create_user,
    update_user,
    delete_user,
    authenticate_user,
    list_users,
    request_password_reset,
    reset_password_with_token,
    logout_user,
    refresh_token,
)
from probe.services.auth import get_current_user, get_admin_user, limiter

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def route_create_user(
    request: Request,
    data: UserCreate,
    db: Session = Depends(get_db),
):
    user = create_user(db, data)
    return {"user": user}


@router.post("/login")
@limiter.limit("10/minute")
def route_login(request: Request, email: str, password: str, db: Session = Depends(get_db)):
    return authenticate_user(db, email, password)


@router.post("/refresh-token")
@limiter.limit("10/minute")
def route_refresh_token(request: Request, refresh_token: str = HTTPBearer(), db: Session = Depends(get_db)):
    return refresh_token(db, refresh_token.credentials)


@router.post("/logout")
@limiter.limit("10/minute")
def route_logout(request: Request, refresh_token: str = HTTPBearer(), db: Session = Depends(get_db)):
    return logout_user(db, refresh_token.credentials)


@router.post("/forgot-password")
@limiter.limit("5/minute")
def route_forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return request_password_reset(db, data)


@router.post("/reset-password")
@limiter.limit("5/minute")
def route_reset_password(
    request: Request,
    data: ResetPasswordConfirm,
    db: Session = Depends(get_db),
):
    return reset_password_with_token(db, data)


@router.get("/", response_model=list[UserRead])
@limiter.limit("30/minute")
def route_list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    return list_users(db, current_user)


@router.get("/{user_id}", response_model=UserRead)
@limiter.limit("60/minute")
def route_get_user(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_user(db, user_id, current_user)


@router.patch("/{user_id}", response_model=UserRead)
@limiter.limit("10/minute")
def route_update_user(
    request: Request,
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_user(db, user_id, data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def route_delete_user(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    delete_user(db, user_id, current_user)
