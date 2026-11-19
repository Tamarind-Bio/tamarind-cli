from enum import Enum


class PipelineRunStatus(str, Enum):
    FAILED = "failed"
    FINISHED = "finished"
    PARTIAL = "partial"
    QUEUED = "queued"
    RUNNING = "running"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return str(self.value)
