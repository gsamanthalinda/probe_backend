import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .enums import DeviceStatus


from database import Base, TimestampMixin
class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number = Column(String, unique=True, nullable=False)
    recycler_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    error_code = Column(String, nullable=True)
    channel = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(DeviceStatus), nullable=False)

    user = relationship("User", back_populates="devices")
    batteries = relationship("Battery", back_populates="device")
    sensor_readings = relationship("SensorReading", back_populates="device")