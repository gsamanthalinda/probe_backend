from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID


from probe.repositories.booking import booking_repository
from probe.repositories.user import user_repository
from probe.repositories.battery import battery_repository
from probe.repositories.sensor_reading import SensorReadingRepository
from probe.schemas.booking import BookingCreate, BookingUpdate,BookingRead
from probe.models.enums import ReadingStatus, BookingStatus


def get_booking(db: Session, booking_id: UUID, current_user=None):
    booking = booking_repository.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking record not found")
    return booking

def list_bookings(db: Session, current_user=None):
   bookings = booking_repository.get_all(db)
   if current_user and current_user.user_type != "ADMIN":
       bookings = [b for b in bookings if b.user_id == current_user.user_id]
   return bookings

def create_booking(db: Session, data: BookingCreate, current_user=None):
   buyer = user_repository.get_by_id(db, data.user_id)
   if not buyer or buyer.user_type != "UPS_COMPANY": 
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Access Denied: Account role unauthorized to initialize purchasing transactions."
       )


   battery = battery_repository.get_by_id(db, data.battery_id)
   if not battery:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Target hardware entity profile not found."
       )
       
   latest_reading = SensorReadingRepository.get_latest_by_battery_id(db, data.battery_id)
   if not latest_reading or latest_reading.status != ReadingStatus.REUSABLE:
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="Transaction Conflict: Asset locked by another operational session."
       )

   existing_active_booking = booking_repository.get_active_by_battery_id(db, data.battery_id)
   if existing_active_booking:
       raise HTTPException(
           status_code=status.HTTP_409_CONFLICT,
           detail="Resource Conflict: This battery asset is already bound to an active transaction workflow."
       )


   dumped_data = data.model_dump()
   dumped_data["status"] = BookingStatus.PENDING
   return booking_repository.create(db, dumped_data)

def transition_booking_status(db: Session, booking_id: UUID, new_status: BookingStatus, current_user=None):
    booking = get_booking(db, booking_id)
    if booking.status == BookingStatus.COMPLETED or booking.status == BookingStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow violation: Terminal booking states cannot be transitioned."
        )
    return booking_repository.update(db, booking, {"status": new_status})

def update_booking(db: Session, booking_id: UUID, data: BookingUpdate, current_user=None):
   booking = get_booking(db, booking_id)
   return booking_repository.update(db, booking, data.model_dump(exclude_unset=True))


def delete_booking(db: Session, booking_id: UUID, current_user=None):
   booking = get_booking(db, booking_id)
   booking_repository.delete(db, booking)
