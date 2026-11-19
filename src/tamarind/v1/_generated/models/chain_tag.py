from enum import Enum


class ChainTag(str, Enum):
    HEAVY = "heavy"
    LEAD = "lead"
    LIGHT = "light"

    def __str__(self) -> str:
        return str(self.value)
