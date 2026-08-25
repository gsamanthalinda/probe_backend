import uuid
from fastapi import APIRouter, Depends, status, HTTPException, Query, Request
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
   delete_battery,
   get_available_by_chemistry
)
from probe.services.auth import get_current_user, get_admin_user, limiter


router = APIRouter(prefix="/batteries", tags=["batteries"])


@router.get("/reference-library", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def route_get_reference_library(request: Request):
    return scraped_18650_reference_sheet


@router.get("/", response_model=list[BatteryRead])
@limiter.limit("60/minute")
def route_list_batteries(
    request: Request,
    device_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
   return list_batteries(db, device_id=device_id, current_user=current_user)


@router.get("/availability/chemistry", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def route_get_available_by_chemistry(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return get_available_by_chemistry(db, current_user)


@router.get("/search/suggestions", response_model=list[str])
@limiter.limit("60/minute")
def route_search_batteries(request: Request, q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    results = search_batteries(db, q)
    return [b.chemistry for b in results]


@router.get("/{battery_id}", response_model=BatteryRead)
@limiter.limit("60/minute")
def route_get_battery(
    request: Request,
    battery_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_battery(db, battery_id, current_user)


@router.post("/", response_model=BatteryRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def route_create_battery(
    request: Request,
    data: BatteryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_type not in ["ADMIN", "RECYCLER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN or RECYCLER can create batteries")
    return create_battery(db, data, current_user)



@router.patch("/{battery_id}", response_model=BatteryRead)
@limiter.limit("20/minute")
def route_update_battery(
    request: Request,
    battery_id: uuid.UUID,
    data: BatteryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_battery(db, battery_id, data, current_user)
    


@router.delete("/{battery_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def route_delete_battery(
    request: Request,
    battery_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
     delete_battery(db, battery_id, current_user)
 