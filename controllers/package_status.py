from enum import Enum

class PackageStatus(str, Enum):
    INSTALLED = "Installed"
    NOT_INSTALLED = "Not Installed"
    UPDATE_AVAILABLE = "Update Available"
    INVALID = "Invalid"
    READY = "Ready"

    def __str__(self) -> str:
        return self.value
