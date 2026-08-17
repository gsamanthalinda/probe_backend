from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from typing import cast


from probe.repositories.device import DeviceRepository
from probe.repositories.user import UserRepository
from probe.models.enums import UserType
from probe.schemas.device import DeviceCreate, DeviceUpdate


def get_device(db: Session, device_id: UUID, current_user=None):
    device = DeviceRepository.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


def get_device_by_serial_number(db: Session, serial_number: str, current_user=None):
    device = DeviceRepository.get_by_serial_number(db, serial_number)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


def list_devices(db: Session, current_user=None):
    devices = DeviceRepository.get_all(db)
    if current_user and current_user.user_type != "ADMIN":
        devices = [d for d in devices if d.recycler_id == current_user.user_id]
    return devices


def create_device(db: Session, data: DeviceCreate, current_user=None):
    clean_serial_number = data.serial_number.strip()
    clean_channel = data.channel.strip()
    clean_status = data.status.value.strip() if hasattr(data.status, 'value') else str(data.status).strip()

    if not clean_serial_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial number cannot be empty or whitespace."
        )

    if DeviceRepository.get_by_serial_number(db, clean_serial_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A device with this serial number already exists."
        )

    if not clean_channel or not clean_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required hardware configuration values cannot be empty or whitespaces."
        )


    recycler = UserRepository.get_by_id(db, data.recycler_id)
    if not recycler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The managing owner user profile does not exist."
        )


    if cast(UserType, recycler.user_type) != UserType.RECYCLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Violation: Only registered recycler entities can manage screening hardware units."
        )

    dumped_data = data.model_dump()
    dumped_data["serial_number"] = clean_serial_number
    dumped_data["channel"] = clean_channel
    dumped_data["status"] = clean_status
    if data.description:
        dumped_data["description"] = data.description.strip()

    return DeviceRepository.create(db, dumped_data)


def update_device(db: Session, device_id: UUID, data: DeviceUpdate, current_user=None):
    device = get_device(db, device_id)
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("serial_number", None)
    update_data.pop("recycler_id", None)
    return DeviceRepository.update(db, device, update_data)


def delete_device(db: Session, device_id: UUID, current_user=None):
    device = get_device(db, device_id)
    return DeviceRepository.delete(db, device)