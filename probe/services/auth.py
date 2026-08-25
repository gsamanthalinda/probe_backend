import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import uuid

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from collections import defaultdict
import pyotp

from database import get_db
from probe.repositories.user import user_repository
from probe.rate_limiter import limiter

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = HTTPBearer()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))

_login_attempts = defaultdict(list)


def _cleanup_old_attempts(email: str):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)
    _login_attempts[email] = [ts for ts in _login_attempts[email] if ts > cutoff]


def record_login_attempt(email: str) -> bool:
    _cleanup_old_attempts(email)
    _login_attempts[email].append(datetime.now(timezone.utc))
    return len(_login_attempts[email]) >= MAX_LOGIN_ATTEMPTS


def is_locked_out(email: str) -> bool:
    _cleanup_old_attempts(email)
    return len(_login_attempts[email]) >= MAX_LOGIN_ATTEMPTS


def clear_login_attempts(email: str):
    _login_attempts[email] = []


def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password[:72], hashed_password)


def create_access_token(user_id: str, user_type: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "user_type": str(user_type), "exp": expire_at, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, token_version: int) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "token_version": token_version,
        "exp": expire_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def refresh_access_token(db: Session, raw_token: str) -> str:
    try:
        payload = jwt.decode(raw_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    token_version = payload.get("token_version")
    if not user_id or token_version is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token has been revoked")

    return create_access_token(user.user_id, user.user_type)


def revoke_user_tokens(db: Session, user_id: uuid.UUID):
    user = user_repository.get_by_id(db, user_id)
    if user:
        user.token_version = (user.token_version or 0) + 1
        db.commit()
        db.refresh(user)
    return user


def get_current_user(token=Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_admin_user(current_user=Depends(get_current_user)):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="HERckers")


def verify_mfa_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def hash_backup_code(code: str) -> str:
    return pwd_context.hash(code)


def verify_backup_code(hashed_code: str, code: str) -> bool:
    return pwd_context.verify(code, hashed_code)


def generate_backup_codes(count: int = 10) -> tuple[list[str], list[str]]:
    plain_codes = [secrets.token_hex(4) for _ in range(count)]
    hashed_codes = [hash_backup_code(code) for code in plain_codes]
    return plain_codes, hashed_codes


def enable_mfa(db: Session, user_id: uuid.UUID, secret: str, backup_codes: list[str]):
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.mfa_secret = secret
    user.mfa_enabled = True
    user.mfa_backup_codes = ",".join(backup_codes)
    db.commit()
    db.refresh(user)
    return user


def disable_mfa(db: Session, user_id: uuid.UUID):
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = None
    db.commit()
    db.refresh(user)
    return user
