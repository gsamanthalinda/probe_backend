from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from collections import defaultdict

from probe.repositories.battery import battery_repository
from probe.repositories.user import user_repository
from probe.repositories.booking import booking_repository
from probe.schemas.battery import BatteryCreate, BatteryUpdate
from probe.services.battery_utils import scraped_18650_reference_sheet, identify_battery_type
from probe.models.enums import BookingStatus


_valid_battery_names = {item["name"] for item in scraped_18650_reference_sheet}


def get_battery(db: Session, battery_id: UUID, current_user=None):
    battery = battery_repository.get_by_id(db, battery_id)
    if not battery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battery asset target not found")
    return battery


def list_batteries(db: Session, device_id: UUID | None = None, current_user=None):
    if device_id:
        batteries = battery_repository.get_by_device_id(db, device_id)
    else:
        batteries = battery_repository.get_all(db)
    
    if current_user and current_user.user_type == "ADMIN":
        return batteries
    
    if current_user and current_user.user_type == "RECYCLER":
        return [b for b in batteries if b.recycler_id == current_user.user_id]
    
    lithium_only = [
        b for b in batteries 
        if identify_battery_type(b.chemistry) is not None
    ]
    
    if current_user:
        lithium_only = [b for b in lithium_only if b.recycler_id == current_user.user_id]
    
    return lithium_only


def search_batteries(db: Session, query: str, limit: int = 10, current_user=None):
    return battery_repository.search_by_chemistry(db, query, limit)


def get_available_by_chemistry(db: Session):
    batteries = battery_repository.get_all(db)
    active_bookings = booking_repository.get_active_bookings(db)
    
    booked_battery_ids = {b.battery_id for b in active_bookings}
    
    available = [b for b in batteries if b.battery_id not in booked_battery_ids]
    
    chemistry_map = defaultdict(lambda: {"total": 0, "available": 0, "category_a": 0, "category_b": 0, "category_c": 0})
    
    for b in available:
        chemistry = b.chemistry
        chemistry_map[chemistry]["available"] += b.quantity
        chemistry_map[chemistry]["total"] += b.quantity
        
        if hasattr(b, 'category') and b.category:
            if b.category == "A":
                chemistry_map[chemistry]["category_a"] += b.quantity
            elif b.category == "B":
                chemistry_map[chemistry]["category_b"] += b.quantity
            elif b.category == "C":
                chemistry_map[chemistry]["category_c"] += b.quantity
    
    for b in batteries:
        if b.battery_id in booked_battery_ids:
            chemistry = b.chemistry
            chemistry_map[chemistry]["total"] += b.quantity
    
    return dict(chemistry_map)


def create_battery(db: Session, data: BatteryCreate, current_user=None):
    clean_chemistry = data.chemistry.strip()

    if not clean_chemistry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Battery profile fields cannot consist of empty parameters."
        )

    if clean_chemistry not in _valid_battery_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected battery type is not recognized. Please choose from the approved reference library."
        )

    recycler = user_repository.get_by_id(db, data.recycler_id)
    if not recycler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid asset assignment: Target recycler profile must exist and hold proper credentials."
        )

    dumped_data = data.model_dump()
    dumped_data["chemistry"] = clean_chemistry

    return battery_repository.create(db, dumped_data)


def update_battery(db: Session, battery_id: UUID, data: BatteryUpdate, current_user=None):
    battery = get_battery(db, battery_id)
    return battery_repository.update(db, battery, data.model_dump(exclude_unset=True))


def delete_battery(db: Session, battery_id: UUID, current_user=None):
    battery = get_battery(db, battery_id)
    if battery:
        battery_repository.delete(db, battery)
