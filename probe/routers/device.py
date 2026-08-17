import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from probe.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from probe.services.device import (
    get_device,
    get_device_by_serial_number,
    list_devices,
    create_device,
    update_device,
    delete_device
)
from probe.services.battery import list_batteries
from probe.services.auth import get_current_user, get_admin_user


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=list[DeviceRead])
def route_list_devices(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_devices(db, current_user)


@router.get("/{device_id}", response_model=DeviceRead)
def route_get_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_device(db, device_id, current_user)


@router.get("/{device_id}/batteries", response_model=list)
def route_get_device_batteries(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    batteries = list_batteries(db, device_id=device_id, current_user=current_user)
    return [
        {
            "battery_id": str(b.battery_id),
            "chemistry": b.chemistry,
            "recycler_id": str(b.recycler_id),
            "device_id": str(b.device_id),
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in batteries
    ]


@router.get("/by-serial-number/{serial_number}", response_model=DeviceRead)
def route_get_device_by_serial_number(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_device_by_serial_number(db, serial_number, current_user)


@router.post("/", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def route_create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_type not in ["ADMIN", "RECYCLER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN or RECYCLER can create devices")
    return create_device(db, data, current_user)


@router.patch("/{device_id}", response_model=DeviceRead)
def route_update_device(
    device_id: uuid.UUID,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_device(db, device_id, data, current_user)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def route_delete_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    delete_device(db, device_id, current_user)