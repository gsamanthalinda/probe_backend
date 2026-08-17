import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from probe.schemas.booking import BookingCreate, BookingRead, BookingUpdate
from probe.models.enums import BookingStatus


from probe.services.booking import (
   get_booking,
   list_bookings,
   create_booking,
   update_booking,
   delete_booking,
   transition_booking_status
)
from probe.services.auth import get_current_user, get_admin_user


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=list[BookingRead])
def route_list_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
   return list_bookings(db, current_user)


@router.get("/{booking_id}", response_model=BookingRead)
def route_get_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_booking(db, booking_id, current_user)
    


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def route_create_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
         return create_booking(db, data, current_user)


@router.post("/{booking_id}/transition/{new_status}", response_model=BookingRead)
def route_transition_booking(
    booking_id: uuid.UUID,
    new_status: BookingStatus,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    return transition_booking_status(db, booking_id, new_status, current_user)


@router.patch("/{booking_id}", response_model=BookingRead)
def route_update_booking(
    booking_id: uuid.UUID,
    data: BookingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
   return update_booking(db, booking_id, data, current_user)
   


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def route_delete_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    delete_booking(db, booking_id, current_user)

