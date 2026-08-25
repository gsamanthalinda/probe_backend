from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from probe.schemas.sensor_reading import SensorReadingCreate, SensorReadingResponse, SensorReadingUpdate
from probe.services.sensor_reading import SensorReadingService
from probe.services.auth import get_current_user, get_admin_user, limiter

router = APIRouter(prefix="/v1/sensor-readings", tags=["Sensor Readings"])

@router.post("/", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def record_hardware_telemetry(
   request: Request,
   payload: SensorReadingCreate,
   db: Session = Depends(get_db)
):
   return SensorReadingService.create_sensor_reading(db, payload)


@router.get("/{sensor_reading_id}", response_model=SensorReadingResponse)
@limiter.limit("60/minute")
def get_sensor_reading(
    request: Request,
    sensor_reading_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return SensorReadingService.get_sensor_reading(db, sensor_reading_id, current_user)

@router.patch("/{sensor_reading_id}", response_model=SensorReadingResponse)
@limiter.limit("20/minute")
def update_sensor_reading(
    request: Request,
    sensor_reading_id: UUID,
    payload: SensorReadingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    return SensorReadingService.update_sensor_reading(db, sensor_reading_id, payload)

@router.get("/device/{device_id}", response_model=list[SensorReadingResponse])
@limiter.limit("60/minute")
def list_readings_by_device(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
   return SensorReadingService.get_readings_by_device(db, device_id, current_user)


@router.get("/battery/{battery_id}", response_model=list[SensorReadingResponse])
@limiter.limit("60/minute")
def list_readings_by_battery(
    request: Request,
    battery_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
   return SensorReadingService.get_readings_by_battery(db, battery_id, current_user)

@router.delete("/{sensor_reading_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_sensor_reading(
    request: Request,
    sensor_reading_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    SensorReadingService.delete_sensor_reading(db, sensor_reading_id)
    return None
