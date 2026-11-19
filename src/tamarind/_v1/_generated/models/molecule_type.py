from enum import Enum


class MoleculeType(str, Enum):
    ANTIBODY = "antibody"
    ENZYME = "enzyme"
    NUCLEIC_ACID = "nucleic_acid"
    PEPTIDE = "peptide"
    PROTEIN = "protein"
    SMALL_MOLECULE = "small_molecule"
    SMALL_MOLECULE_BINDING_PROTEIN = "small_molecule_binding_protein"

    def __str__(self) -> str:
        return str(self.value)
