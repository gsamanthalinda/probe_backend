from datetime import datetime
from uuid import UUID
from .enums import BookingStatus


from pydantic import BaseModel, ConfigDict, Field


class BookingBase(BaseModel):
   user_id: UUID
   battery_id: UUID
   quantity: int = Field(default=1, ge=1)
    
class BookingCreate(BookingBase):
   pass


class BookingUpdate(BaseModel):
   user_id: UUID | None = None
   battery_id: UUID | None = None
   quantity: int | None = Field(None, ge=1)
     
class BookingRead(BookingBase):
   model_config = ConfigDict(from_attributes=True)
   
   booking_id: UUID
   created_at: datetime
   status: BookingStatus