import uuid
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Enum,
    String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .enums import ReadingStatus

from database import Base, TimestampMixin



class SensorReading(Base, TimestampMixin):
    __tablename__ = "sensor_readings"

    sensor_reading_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    battery_id = Column(UUID(as_uuid=True), ForeignKey("batteries.battery_id"), nullable=False)
    temp = Column(Float, nullable=False)
    voltage = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    state_of_health = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    status = Column(Enum(ReadingStatus), nullable=False)



    device = relationship("Device", back_populates="sensor_readings")
    battery = relationship("Battery", back_populates="sensor_readings")