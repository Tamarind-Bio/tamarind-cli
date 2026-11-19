from enum import Enum


class ListAssaysScope(str, Enum):
    MINE = "mine"
    ORG = "org"

    def __str__(self) -> str:
        return str(self.value)
