import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base, TimestampMixin



class Battery(Base, TimestampMixin):
    __tablename__ = "batteries"

    battery_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chemistry = Column(String, nullable=False)
    recycler_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)



    recycler = relationship("User", back_populates="batteries")
    device = relationship("Device", back_populates="batteries")
    sensor_readings = relationship("SensorReading", back_populates="battery")
    bookings = relationship("Booking", back_populates="battery")