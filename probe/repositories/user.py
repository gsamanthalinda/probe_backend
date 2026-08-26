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
        if not email or len(email) > 255:
            return None
        return db.query(self.model).filter(self.model.email == email.strip().lower()).first()

    def get_by_reset_token(self, db: Session, token: str):
        if not token or len(token) > 255:
            return None
        return db.query(self.model).filter(self.model.reset_token == token.strip()).first()

    def create(self, db: Session, data: dict):
        user = self.model(**data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, db_obj: User, data: dict):
        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: User):
        db.delete(db_obj)
        db.commit()

    def disable_mfa(self, db: Session, db_obj: User):
        db_obj.mfa_enabled = False
        db_obj.mfa_secret = None
        db_obj.mfa_backup_codes = None
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def setup_mfa(self, db: Session, db_obj: User, secret: str, hashed_backup_codes: str):
        db_obj.mfa_secret = secret
        db_obj.mfa_backup_codes = hashed_backup_codes
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def enable_mfa(self, db: Session, db_obj: User):
        db_obj.mfa_enabled = True
        db.commit()
        db.refresh(db_obj)
        return db_obj

user_repository = UserRepository()
