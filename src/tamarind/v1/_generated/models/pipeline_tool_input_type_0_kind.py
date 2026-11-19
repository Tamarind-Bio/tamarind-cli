from enum import Enum


class PipelineToolInputType0Kind(str, Enum):
    RAWSEQUENCE = "rawSequence"

    def __str__(self) -> str:
        return str(self.value)
