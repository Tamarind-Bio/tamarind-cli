from enum import Enum


class SubmitFileBatchRequestKind(str, Enum):
    BATCH = "batch"

    def __str__(self) -> str:
        return str(self.value)
