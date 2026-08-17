import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

LOCAL_DATABASE_URL = os.getenv("database_url", "postgresql://postgres:postgres@localhost:5432/probe-db")

database_url = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url, pool_pre_ping=True, future=True)

session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()
