import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .enums import BookingStatus

from database import Base, TimestampMixin
class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    booking_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    battery_id = Column(UUID(as_uuid=True), ForeignKey("batteries.battery_id"), nullable=False)
    status = Column(Enum(BookingStatus), nullable=False)

    buyer = relationship("User", back_populates="bookings")
    battery = relationship("Battery", back_populates="bookings")