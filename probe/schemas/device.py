from datetime import datetime
from uuid import UUID
from probe.models.enums import DeviceStatus
from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
   serial_number: str
   recycler_id: UUID
   channel: str
   description: str | None = None
   status:DeviceStatus 
  
class DeviceCreate(DeviceBase):
   pass


class DeviceUpdate(BaseModel):
    channel: str | None = None
    description: str | None = None
    status: DeviceStatus | None = None
    
class DeviceRead(DeviceBase):
   model_config = ConfigDict(from_attributes=True)
   
   device_id: UUID
   created_at: datetime
   error_code: str | None = None