import uuid

from sqlalchemy.orm import Session

from probe.models.battery import Battery


class BatteryRepository:
    def __init__(self):
        self.model = Battery

    def get_by_id(self, db: Session, id: uuid.UUID):
        return db.get(self.model, id)

    def get_all(self, db: Session):
        return db.query(self.model).all()

    def get_by_device_id(self, db: Session, device_id: uuid.UUID):
        return db.query(self.model).filter(self.model.device_id == device_id).all()

    def search_by_chemistry(self, db: Session, query: str, limit: int = 10):
        if not query or not query.strip():
            return []
        safe_query = query.strip()[:100]
        return (
            db.query(self.model)
            .filter(self.model.chemistry.ilike(f"%{safe_query}%"))
            .limit(max(1, min(limit, 100)))
            .all()
        )

    def create(self, db: Session, data: dict):
        battery = self.model(**data)
        db.add(battery)
        db.commit()
        db.refresh(battery)
        return battery

    def update(self, db: Session, db_obj: Battery, data: dict) -> Battery:
        allowed_fields = {"chemistry", "quantity", "recycler_id", "device_id"}
        for field, value in data.items():
            if field in allowed_fields and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: Battery):
        db.delete(db_obj)
        db.commit()
        return True


battery_repository = BatteryRepository()
