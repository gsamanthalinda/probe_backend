import uuid
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from probe.schemas.battery import BatteryCreate, BatteryRead, BatteryUpdate
from probe.services.battery_utils import scraped_18650_reference_sheet


from probe.services.battery import (
   get_battery,
   list_batteries,
   search_batteries,
   create_battery,
   update_battery,
   delete_battery
)
from probe.services.auth import get_current_user, get_admin_user


router = APIRouter(prefix="/batteries", tags=["batteries"])


@router.get("/reference-library", status_code=status.HTTP_200_OK)
def route_get_reference_library():
    return scraped_18650_reference_sheet


@router.get("/", response_model=list[BatteryRead])
def route_list_batteries(
    device_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
   return list_batteries(db, device_id=device_id, current_user=current_user)


@router.get("/search/suggestions", response_model=list[str])
def route_search_batteries(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    results = search_batteries(db, q)
    return [b.chemistry for b in results]


@router.get("/{battery_id}", response_model=BatteryRead)
def route_get_battery(
    battery_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_battery(db, battery_id, current_user)


@router.post("/", response_model=BatteryRead, status_code=status.HTTP_201_CREATED)
def route_create_battery(
    data: BatteryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_type not in ["ADMIN", "RECYCLER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN or RECYCLER can create batteries")
    return create_battery(db, data, current_user)



@router.patch("/{battery_id}", response_model=BatteryRead)
def route_update_battery(
    battery_id: uuid.UUID,
    data: BatteryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_battery(db, battery_id, data, current_user)
   


@router.delete("/{battery_id}", status_code=status.HTTP_204_NO_CONTENT)
def route_delete_battery(
    battery_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
     delete_battery(db, battery_id, current_user)
 