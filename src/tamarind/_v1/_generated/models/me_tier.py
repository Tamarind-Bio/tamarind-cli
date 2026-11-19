from enum import Enum


class MeTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"

    def __str__(self) -> str:
        return str(self.value)
