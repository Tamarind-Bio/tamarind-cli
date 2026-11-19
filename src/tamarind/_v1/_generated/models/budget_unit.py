from enum import Enum


class BudgetUnit(str, Enum):
    WEIGHTEDHOURS = "weightedHours"

    def __str__(self) -> str:
        return str(self.value)
