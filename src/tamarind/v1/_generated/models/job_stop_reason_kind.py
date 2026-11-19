from enum import Enum


class JobStopReasonKind(str, Enum):
    CANCELED = "canceled"
    ERROR = "error"
    LIMIT = "limit"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
