from enum import Enum


class ListPipelineRunsSourceType0(str, Enum):
    PRODUCTION = "production"
    TEST = "test"

    def __str__(self) -> str:
        return str(self.value)
