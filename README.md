# HERckers_Backend
HERckers_Backend is a FastAPI-based backend service for managing a device and battery lifecycle ecosystem. It provides a RESTful API for user management, device tracking, battery registration, booking workflows, and sensor reading ingestion, tailored for organizations that operate across admin, recycler, and UPS company roles. The service connects to a PostgreSQL database via SQLAlchemy and includes support for migrations using Alembic.

## Overview
HERckers_Backend exposes a RESTful API that enables three user types — ADMIN, RECYCLER, and UPS_COMPANY — to interact with shared resources. The service enforces role-based access control, rate limiting, request size limits, and secure defaults out of the box. Users can register, authenticate, and manage their profiles. The API supports JWT-based authentication with refresh tokens, password reset flows, and optional multi-factor authentication (MFA) via TOTP. Admin users can list, update, and delete users across the platform.

Devices represent tracked hardware units and are associated with a user or company. The device endpoints support full CRUD operations, lookup by serial number, and querying associated batteries. Only ADMIN and RECYCLER roles can create new devices. Batteries are linked to specific devices and recyclers. The API supports listing batteries for a device and managing battery metadata including chemistry type and recycler assignment.

Bookings enable scheduling and tracking of device or battery lifecycle events. Bookings progress through defined statuses — PENDING, CONFIRMED, CANCELED, and COMPLETED — and support status transitions. Admin-level users manage bookings, while authenticated users can create them. The platform also ingests sensor readings from devices and classifies them by status: REUSABLE, RECOVERABLE, or DISPOSABLE. These readings support decision-making around device and battery reuse or disposal.

## Tech Stack
The project is built with FastAPI for web framework and routing, Uvicorn as the ASGI server, SQLAlchemy for ORM and database toolkit, PostgreSQL as the primary database, Alembic for database migrations, Pydantic for data validation and settings, python-jose for JWT token handling, bcrypt and passlib for password hashing, slowapi for rate limiting, python-dotenv for environment configuration, Pillow for image handling used for MFA QR codes, and paho-mqtt for MQTT messaging used for sensor ingestion.

## Getting Started
Prerequisites
The application requires Python 3.11 or higher, a running PostgreSQL instance, and pip or a compatible package manager.

### Installation
To install the project, first clone the repository. Then install dependencies with pip install -r requirements.txt. If using Alembic for database migrations, apply them with alembic upgrade head.

### Environment Variables
The application reads configuration from environment variables. Required variables include DATABASE_URL for the PostgreSQL connection string, CORS_ORIGINS as a comma-separated list of allowed CORS origins, SECRET_KEY for JWT signing, ALGORITHM for JWT signing algorithm which defaults to HS256, ACCESS_TOKEN_EXPIRE_MINUTES for access token TTL, and REFRESH_TOKEN_EXPIRE_DAYS for refresh token TTL.

### Running the Application
Start the development server with Uvicorn using uvicorn main:app --reload --host 0.0.0.0 --port 8000. For production deployments, a Procfile is included that runs uvicorn main:app --host 0.0.0.0 --port $PORT.

## API Documentation
When the application is running, interactive API documentation is available at Swagger UI at /docs, ReDoc at /redoc, and the OpenAPI JSON at /openapi.json.

## Project Structure

HERckers_Backend/
├── main.py                 # Application entry point, middleware, and router registration
├── database.py             # Database engine, session factory, and base model
├── requirements.txt        # Python dependencies
├── Procfile                # Production process declaration for uvicorn
├── pyrightconfig.json      # Static type-checking configuration
├── .env                    # Environment variables (gitignored)
├── .gitignore              # Git ignore rules
├── .python-version         # Pinned Python runtime version
├── package.json            # Node metadata for tooling or scripts
├── package-lock.json       # Node lockfile
├── .github/                # GitHub Actions workflows and repo config
├── .kilo/                  # Kilo workspace configuration
├── probe/                  # Core application package
│   ├── __init__.py
│   ├── rate_limiter.py     # SlowAPI limiter and exception handler setup
│   ├── dependencies.py     # Shared FastAPI dependencies
│   ├── routers/            # API route handlers
│   │   ├── __init__.py
│   │   ├── user.py         # User auth, profile, and MFA routes
│   │   ├── device.py       # Device CRUD and lookup routes
│   │   ├── battery.py      # Battery management routes
│   │   ├── booking.py      # Booking and status-transition routes
│   │   └── sensor_reading.py # Sensor reading ingestion routes
│   ├── services/           # Business logic layer
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── battery.py
│   │   ├── booking.py
│   │   └── sensor_reading.py
│   ├── repositories/       # Data access layer
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── battery.py
│   │   ├── booking.py
│   │   └── sensor_reading.py
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── enums.py        # Shared enumerations
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── battery.py
│   │   ├── booking.py
│   │   └── sensor_reading.py
│   └── schemas/            # Pydantic request and response schemas
│       ├── __init__.py
│       ├── enums.py
│       ├── user.py
│       ├── device.py
│       ├── booking.py
│       └── sensor_reading.py
└── README.md
