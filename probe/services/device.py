from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from typing import cast


from probe.repositories.device import DeviceRepository
from probe.repositories.user import user_repository
from probe.models.enums import UserType
from probe.schemas.device import DeviceCreate, DeviceUpdate


def get_device(db: Session, device_id: UUID, current_user=None):
    device = DeviceRepository.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if current_user and current_user.user_type != "ADMIN" and device.recycler_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this device")

    return device


def get_device_by_serial_number(db: Session, serial_number: str, current_user=None):
    device = DeviceRepository.get_by_serial_number(db, serial_number)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if current_user and current_user.user_type != "ADMIN" and device.recycler_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this device")

    return device


def list_devices(db: Session, current_user=None):
    devices = DeviceRepository.get_all(db)
    if current_user and current_user.user_type != "ADMIN":
        devices = [d for d in devices if d.recycler_id == current_user.user_id]
    return devices


def create_device(db: Session, data: DeviceCreate, current_user=None):
    if current_user.user_type not in ["ADMIN", "RECYCLER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN or RECYCLER can create devices")

    clean_serial_number = data.serial_number.strip()
    clean_channel = data.channel.strip()
    clean_status = data.status.value.strip() if hasattr(data.status, 'value') else str(data.status).strip()

    if not clean_serial_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial number cannot be empty or whitespace."
        )

    if len(clean_serial_number) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial number exceeds maximum length."
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

    if len(clean_channel) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel name exceeds maximum length."
        )

    recycler = user_repository.get_by_id(db, id=data.recycler_id)
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
        dumped_data["description"] = data.description.strip()[:500] if data.description else None

    return DeviceRepository.create(db, dumped_data)


def update_device(db: Session, device_id: UUID, data: DeviceUpdate, current_user=None):
    device = get_device(db, device_id, current_user)

    if current_user and current_user.user_type != "ADMIN" and device.recycler_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only device owner or ADMIN can update devices")

    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("serial_number", None)
    update_data.pop("recycler_id", None)
    return DeviceRepository.update(db, device, update_data)


def delete_device(db: Session, device_id: UUID, current_user=None):
    device = get_device(db, device_id, current_user)

    if current_user and current_user.user_type != "ADMIN" and device.recycler_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only device owner or ADMIN can delete devices")

    return DeviceRepository.delete(db, device)