from enum import Enum


class JobStatus(str, Enum):
    COMPLETE = "Complete"
    FAILED = "Failed"
    IN_QUEUE = "In Queue"
    RUNNING = "Running"
    STOPPED = "Stopped"

    def __str__(self) -> str:
        return str(self.value)
