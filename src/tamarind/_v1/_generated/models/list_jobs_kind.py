from enum import Enum


class ListJobsKind(str, Enum):
    BATCH = "batch"
    JOB = "job"
    PIPELINE = "pipeline"

    def __str__(self) -> str:
        return str(self.value)
