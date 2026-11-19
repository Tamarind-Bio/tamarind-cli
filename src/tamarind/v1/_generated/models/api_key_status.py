from enum import Enum


class ApiKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"

    def __str__(self) -> str:
        return str(self.value)
