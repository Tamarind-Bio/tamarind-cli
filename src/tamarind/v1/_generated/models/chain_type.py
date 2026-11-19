from enum import Enum


class ChainType(str, Enum):
    PROTEIN = "protein"
    SMALL_MOLECULE = "small_molecule"

    def __str__(self) -> str:
        return str(self.value)
