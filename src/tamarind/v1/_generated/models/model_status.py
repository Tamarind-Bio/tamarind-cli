from enum import Enum


class ModelStatus(str, Enum):
    AVAILABLE = "available"
    FAILED = "failed"
    TRAINING = "training"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
