from enum import Enum


class SubmitInlineBatchRequestKind(str, Enum):
    BATCH = "batch"

    def __str__(self) -> str:
        return str(self.value)
