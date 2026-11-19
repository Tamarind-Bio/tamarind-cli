from enum import Enum


class MoleculeClass(str, Enum):
    NUCLEIC_ACID = "nucleic_acid"
    PROTEIN = "protein"
    SMALL_MOLECULE = "small_molecule"

    def __str__(self) -> str:
        return str(self.value)
