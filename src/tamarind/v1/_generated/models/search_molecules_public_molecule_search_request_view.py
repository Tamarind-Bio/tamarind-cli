from enum import Enum


class SearchMoleculesPublicMoleculeSearchRequestView(str, Enum):
    CARD = "card"
    FULL = "full"

    def __str__(self) -> str:
        return str(self.value)
