from enum import Enum


class SubmitJobRequestKind(str, Enum):
    JOB = "job"

    def __str__(self) -> str:
        return str(self.value)
