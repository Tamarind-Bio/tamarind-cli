from enum import Enum


class NodeRunStatus(str, Enum):
    CANCELLED = "cancelled"
    FAILED = "failed"
    FINISHED = "finished"
    QUEUED = "queued"
    RUNNING = "running"
    SKIPPED = "skipped"
    STOPPED = "stopped"
    WAITING = "waiting"

    def __str__(self) -> str:
        return str(self.value)
