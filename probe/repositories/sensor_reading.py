from sqlalchemy.orm import Session
from uuid import UUID
from probe.models.sensor_reading import SensorReading


class SensorReadingRepository:
    @staticmethod
    def get_by_id(db: Session, sensor_reading_id: UUID) -> SensorReading | None:
        return db.query(SensorReading).filter(SensorReading.sensor_reading_id == sensor_reading_id).first()

    @staticmethod
    def get_all(db: Session) -> list[SensorReading]:
        return db.query(SensorReading).all()

    @staticmethod
    def get_latest_by_battery_id(db: Session, battery_id: UUID) -> SensorReading | None:
        return (
            db.query(SensorReading)
            .filter(SensorReading.battery_id == battery_id)
            .order_by(SensorReading.created_at.desc())
            .first()
        )

    @staticmethod
    def get_by_device_id(db: Session, device_id: UUID) -> list[SensorReading]:
        return db.query(SensorReading).filter(SensorReading.device_id == device_id).all()

    @staticmethod
    def get_by_battery_id(db: Session, battery_id: UUID) -> list[SensorReading]:
        return db.query(SensorReading).filter(SensorReading.battery_id == battery_id).all()

    @staticmethod
    def create(db: Session, data_dict: dict) -> SensorReading:
        db_reading = SensorReading(**data_dict)
        db.add(db_reading)
        db.commit()
        db.refresh(db_reading)
        return db_reading

    @staticmethod
    def update(db: Session, db_obj: SensorReading, update_data: dict) -> SensorReading:
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: SensorReading) -> None:
        db.delete(db_obj)
        db.commit()
