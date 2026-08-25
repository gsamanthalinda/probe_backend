import uuid
from sqlalchemy import(
    Column,
    String,
    Enum,
    DateTime,
    Boolean,
    Integer
)
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base, TimestampMixin
from .enums import UserType


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    company_name = Column(String, nullable=False)
    reset_token = Column(String, nullable=True, index=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String, nullable=True)
    mfa_backup_codes = Column(String, nullable=True)
    token_version = Column(Integer, default=1, nullable=False)

    devices = relationship("Device", back_populates="user")
    batteries = relationship("Battery", back_populates="recycler")
    bookings = relationship("Booking", back_populates="buyer")