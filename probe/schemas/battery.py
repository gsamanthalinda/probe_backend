from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict



class BatteryBase(BaseModel):
   recycler_id: UUID
   device_id: UUID
   chemistry: str
   
class BatteryCreate(BatteryBase):
     pass


class BatteryUpdate(BaseModel):
    chemistry: str | None = None
    recycler_id: UUID | None = None
    device_id: UUID | None = None
     
class BatteryRead(BatteryBase):
     model_config = ConfigDict(from_attributes=True)
     battery_id: UUID
     created_at: datetime