from datetime import datetime
from uuid import UUID
from probe.models.enums import DeviceStatus
from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
   serial_number: str = Field(..., min_length=1, max_length=100)
   recycler_id: UUID
   channel: str = Field(..., min_length=1, max_length=50)
   description: str | None = Field(None, max_length=500)
   status: DeviceStatus

class DeviceCreate(DeviceBase):
   pass


class DeviceUpdate(BaseModel):
    channel: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=500)
    status: DeviceStatus | None = None

class DeviceRead(DeviceBase):
   model_config = ConfigDict(from_attributes=True)

   device_id: UUID
   created_at: datetime
   error_code: str | None = Field(None, max_length=100)