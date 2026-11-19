from enum import Enum


class MoleculeMatchDetailAxis(str, Enum):
    PROPERTY = "property"
    SCORE = "score"

    def __str__(self) -> str:
        return str(self.value)
