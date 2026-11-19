from enum import Enum


class ApiKeyBudgetPeriod(str, Enum):
    MONTH = "month"
    TOTAL = "total"

    def __str__(self) -> str:
        return str(self.value)
