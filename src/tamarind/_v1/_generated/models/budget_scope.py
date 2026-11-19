from enum import Enum


class BudgetScope(str, Enum):
    APIKEY = "apiKey"
    CONTRACT = "contract"
    MEMBER = "member"
    MODEL = "model"
    ORGANIZATION = "organization"
    TEAM = "team"

    def __str__(self) -> str:
        return str(self.value)
