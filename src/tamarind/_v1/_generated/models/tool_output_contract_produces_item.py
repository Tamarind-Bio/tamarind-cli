from enum import Enum


class ToolOutputContractProducesItem(str, Enum):
    PDB = "pdb"
    SDF = "sdf"
    SEQUENCE = "sequence"
    SMILES = "smiles"

    def __str__(self) -> str:
        return str(self.value)
