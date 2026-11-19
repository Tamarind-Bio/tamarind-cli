from enum import Enum


class PipelineToolInputType3Kind(str, Enum):
    GROUPREF = "groupRef"

    def __str__(self) -> str:
        return str(self.value)
