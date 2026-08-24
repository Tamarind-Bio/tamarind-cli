from enum import Enum


class PublicVersionStatus(str, Enum):
    COMPLETE = "Complete"
    QUEUED = "Queued"
    RUNNING = "Running"
    STOPPED = "Stopped"

    def __str__(self) -> str:
        return str(self.value)
