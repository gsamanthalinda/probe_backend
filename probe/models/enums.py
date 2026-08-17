import enum

class UserType(str,enum.Enum):
    ADMIN = "ADMIN"
    RECYCLER = "RECYCLER"
    UPS_COMPANY = "UPS_COMPANY"

class BookingStatus(str,enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"

class DeviceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class ReadingStatus(str, enum.Enum):
    REUSABLE = "REUSABLE"
    RECOVERABLE = "RECOVERABLE"
    DISPOSABLE = "DISPOSABLE"

    
