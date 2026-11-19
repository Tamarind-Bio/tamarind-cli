from enum import Enum


class RefreshUsageResponse202Status(str, Enum):
    REFRESHING = "refreshing"

    def __str__(self) -> str:
        return str(self.value)
