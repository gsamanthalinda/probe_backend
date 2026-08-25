from uuid import UUID

from sqlalchemy.orm import Session

from probe.models.device import Device

class DeviceRepository:
    @staticmethod
    def get_by_id(db: Session, device_id: UUID) -> Device | None:
        return db.query(Device).filter(Device.device_id == device_id).first()

    @staticmethod
    def get_all(db: Session) -> list[Device]:
        return db.query(Device).all()

    @staticmethod
    def get_by_serial_number(db: Session, serial_number: str) -> Device | None:
        if not serial_number or len(serial_number) > 100:
            return None
        return db.query(Device).filter(Device.serial_number == serial_number.strip()).first()

    @staticmethod
    def create(db: Session, data: dict) -> Device:
        device = Device(**data)
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def update(db: Session, device: Device, data: dict) -> Device:
        allowed_fields = {"channel", "description", "status", "error_code"}
        for key, value in data.items():
            if key in allowed_fields and hasattr(device, key):
                setattr(device, key, value)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def delete(db: Session, device: Device) -> Device:
        db.delete(device)
        db.commit()
        return device


device_repository = DeviceRepository()
