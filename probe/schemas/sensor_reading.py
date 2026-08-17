from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from .enums import ReadingStatus


class SensorReadingBase(BaseModel):
   device_id: UUID = Field(..., description="The ESP32 multi-slot physical testing bench ID")
   battery_id: UUID = Field(..., description="The physical battery cell ID being monitored")
   temp: float = Field(..., ge=-40.0, le=120.0, description="Sanitized Celsius telemetry reading")
   current: float = Field(..., ge=0.0, le=100.0, description="Sanitized current monitoring telemetry")

class SensorReadingCreate(SensorReadingBase):
   v_rest: float = Field(..., ge=0.0, le=5.0, description="Open-circuit voltage measured at rest (no load)")
   v_load: float = Field(..., ge=0.0, le=5.0, description="Terminal voltage measured under active discharge load")

class SensorReadingUpdate(BaseModel):
   temp: float | None = Field(None, ge=-40.0, le=120.0)
   current: float | None = Field(None, ge=0.0, le=100.0)
   v_rest: float | None = Field(None, ge=0.0, le=5.0)
   v_load: float | None = Field(None, ge=0.0, le=5.0)

class SensorReadingResponse(SensorReadingBase):
   sensor_reading_id: UUID
   voltage: float = Field(..., description="Stored as v_load (voltage measured while discharging)")
   state_of_health: float = Field(..., description="Calculated State of Health percentage")
   category: str = Field(..., description="Auto-generated quality grade based on SoH")
   status: ReadingStatus = Field(..., description="Auto-generated battery disposition based on category")
   created_at: datetime
   updated_at: datetime

   class Config:
       from_attributes = True
