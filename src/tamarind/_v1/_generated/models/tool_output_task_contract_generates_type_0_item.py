from enum import Enum


class ToolOutputTaskContractGeneratesType0Item(str, Enum):
    PDB = "pdb"
    SDF = "sdf"
    SEQUENCE = "sequence"
    SMILES = "smiles"

    def __str__(self) -> str:
        return str(self.value)
