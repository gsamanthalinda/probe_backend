from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
import math

from ..repositories import SensorReadingRepository, BatteryRepository, DeviceRepository
from ..repositories.booking import booking_repository
from ..schemas.sensor_reading import SensorReadingCreate, SensorReadingUpdate
from ..models.enums import ReadingStatus, BookingStatus

R_NEW = 0.020
R_DEAD = 0.120


class SensorReadingService:

    @staticmethod
    def get_sensor_reading(db: Session, sensor_reading_id: UUID, current_user=None):
        reading = SensorReadingRepository.get_by_id(db, sensor_reading_id)
        if not reading:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Telemetry entry not found"
            )
        
        if current_user and current_user.user_type != "ADMIN":
            battery = BatteryRepository.get_by_id(db, reading.battery_id)
            if not battery or battery.recycler_id != current_user.user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this reading")
        
        return reading

    @staticmethod
    def list_sensor_readings(db: Session):
        return SensorReadingRepository.get_all(db)

    @staticmethod
    def get_readings_by_device(db: Session, device_id: UUID, current_user=None):
        device = DeviceRepository.get_by_id(db, device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        
        if current_user and current_user.user_type != "ADMIN" and device.recycler_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this device")
        
        return SensorReadingRepository.get_by_device_id(db, device_id)

    @staticmethod
    def get_readings_by_battery(db: Session, battery_id: UUID, current_user=None):
        battery = BatteryRepository.get_by_id(db, battery_id)
        if not battery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battery not found")
        
        if current_user and current_user.user_type != "ADMIN" and battery.recycler_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this battery")
        
        return SensorReadingRepository.get_by_battery_id(db, battery_id)

    @staticmethod
    def create_sensor_reading(db: Session, data: SensorReadingCreate):
        device = DeviceRepository.get_by_id(db, data.device_id)
        battery = BatteryRepository.get_by_id(db, data.battery_id)
        if not device or not battery:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hardware Authentication Failure: Unmapped device or battery parameters."
            )

        if str(battery.device_id) != str(data.device_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment Mismatch: Battery is not registered to the specified testing device."
            )

        if data.temp > 42.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Emergency Cutoff: High-temperature hazard detected. Slot offline and asset quarantined."
            )

        if data.current <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid telemetry: discharge current must be greater than zero."
            )

        if data.v_rest < data.v_load:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid telemetry: rest voltage cannot be lower than load voltage."
            )

        try:
            r_i = (data.v_rest - data.v_load) / data.current
            soh_fraction = (R_DEAD - r_i) / (R_DEAD - R_NEW)
            soh_percentage = max(0.0, min(100.0, soh_fraction * 100.0))

            if math.isnan(soh_percentage):
                soh_percentage = 0.0
        except ZeroDivisionError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Calculation failure: division by zero during state-of-health derivation."
            )

        if soh_percentage > 65.0:
            category = "A"
            reading_status = ReadingStatus.REUSABLE
        elif 50.0 <= soh_percentage <= 65.0:
            category = "B"
            reading_status = ReadingStatus.RECOVERABLE
        else:
            category = "C"
            reading_status = ReadingStatus.DISPOSABLE

        if reading_status == ReadingStatus.DISPOSABLE:
            active_booking = booking_repository.get_active_by_battery_id(db, data.battery_id)
            if active_booking:
                booking_repository.update(db, active_booking, {"status": BookingStatus.CANCELED})

        dumped_data = data.model_dump()
        dumped_data["state_of_health"] = soh_percentage
        dumped_data["voltage"] = dumped_data.pop("v_load")
        dumped_data["category"] = category
        dumped_data["status"] = reading_status
        del dumped_data["v_rest"]

        return SensorReadingRepository.create(db, dumped_data)

    @staticmethod
    def update_sensor_reading(db: Session, sensor_reading_id: UUID, data: SensorReadingUpdate):
        reading = SensorReadingService.get_sensor_reading(db, sensor_reading_id)
        update_data = data.model_dump(exclude_unset=True)

        v_rest = data.v_rest
        v_load = data.v_load
        current = data.current if data.current is not None else reading.current

        if v_rest is not None and v_load is not None:
            if current <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid telemetry: discharge current must be greater than zero."
                )

            if v_rest < v_load:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid telemetry: rest voltage cannot be lower than load voltage."
                )

            try:
                r_i = (v_rest - v_load) / current
                soh_fraction = (R_DEAD - r_i) / (R_DEAD - R_NEW)
                soh_percentage = max(0.0, min(100.0, soh_fraction * 100.0))
                if math.isnan(soh_percentage):
                    soh_percentage = 0.0
            except ZeroDivisionError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Calculation failure: division by zero during state-of-health derivation."
                )

            if soh_percentage > 65.0:
                category = "A"
                reading_status = ReadingStatus.REUSABLE
            elif 50.0 <= soh_percentage <= 65.0:
                category = "B"
                reading_status = ReadingStatus.RECOVERABLE
            else:
                category = "C"
                reading_status = ReadingStatus.DISPOSABLE

            if reading_status == ReadingStatus.DISPOSABLE:
                active_booking = booking_repository.get_active_by_battery_id(db, reading.battery_id)
                if active_booking:
                    booking_repository.update(db, active_booking, {"status": BookingStatus.CANCELED})

            update_data["state_of_health"] = soh_percentage
            update_data["voltage"] = v_load
            update_data["category"] = category
            update_data["status"] = reading_status
            del update_data["v_rest"]
            del update_data["v_load"]

        if "battery_id" in update_data and update_data["battery_id"] != reading.battery_id:
            new_battery = BatteryRepository.get_by_id(db, update_data["battery_id"])
            if not new_battery:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target battery entity profile not found."
                )
            if str(new_battery.device_id) != str(reading.device_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignment Mismatch: Battery is not registered to the specified testing device."
                )

        if data.temp is not None and data.temp > 42.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Emergency Cutoff: High-temperature hazard detected. Slot offline and asset quarantined."
            )

        return SensorReadingRepository.update(db, reading, update_data)

    @staticmethod
    def delete_sensor_reading(db: Session, sensor_reading_id: UUID):
        reading = SensorReadingService.get_sensor_reading(db, sensor_reading_id)
        SensorReadingRepository.delete(db, reading)
        return None
