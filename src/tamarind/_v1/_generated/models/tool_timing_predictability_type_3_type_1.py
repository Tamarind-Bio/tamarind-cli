from enum import Enum


class ToolTimingPredictabilityType3Type1(str, Enum):
    PREDICTABLE = "predictable"
    UNPREDICTABLE = "unpredictable"
    VARIABLE = "variable"

    def __str__(self) -> str:
        return str(self.value)
