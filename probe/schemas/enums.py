import enum
class BatteryStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    PROCESSING = "PROCESSING"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"

class UserType(str,enum.Enum):
   RECYCLER = "RECYCLER"
   UPS_COMPANY = "UPS_COMPANY"

class DeviceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class ReadingStatus(str, enum.Enum):
    REUSABLE = "REUSABLE"
    RECOVERABLE = "RECOVERABLE"
    DISPOSABLE = "DISPOSABLE"


