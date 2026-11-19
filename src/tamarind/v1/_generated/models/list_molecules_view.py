from enum import Enum


class ListMoleculesView(str, Enum):
    CARD = "card"
    FULL = "full"

    def __str__(self) -> str:
        return str(self.value)
