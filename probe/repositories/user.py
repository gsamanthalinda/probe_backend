import uuid
from sqlalchemy.orm import Session
from probe.models.user import User

class UserRepository:
    def __init__(self):
        self.model = User

    def get_by_id(self, db: Session, id: uuid.UUID):
        return db.get(self.model, id)

    def get_all(self, db: Session):
        return db.query(self.model).all()

    def get_by_email(self, db: Session, email: str):
        return db.query(self.model).filter(self.model.email == email).first()

    def get_by_reset_token(self, db: Session, token: str):
        return db.query(self.model).filter(self.model.reset_token == token).first()

    def create(self, db: Session, data: dict):
        user = self.model(**data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, db_obj: User, data: dict):
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: User):
        db.delete(db_obj)
        db.commit()

user_repository = UserRepository()
