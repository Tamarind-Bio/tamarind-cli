from enum import Enum


class PipelineFlow(str, Enum):
    FILE = "file"
    MOLECULE = "molecule"

    def __str__(self) -> str:
        return str(self.value)
