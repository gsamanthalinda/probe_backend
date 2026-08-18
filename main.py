import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from probe.routers import user_router
from probe.routers import device_router
from probe.routers import battery_router
from probe.routers import booking_router
from probe.routers import sensor_reading_router
import probe.models as models
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="probe API", version="1.0.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(booking_router)
app.include_router(battery_router)
app.include_router(device_router)
app.include_router(sensor_reading_router)
