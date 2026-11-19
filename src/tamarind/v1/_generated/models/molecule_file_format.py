from enum import Enum


class MoleculeFileFormat(str, Enum):
    AUTO = "auto"
    CSV = "csv"
    FASTA = "fasta"
    PDB = "pdb"
    SDF = "sdf"
    SDF_ZIP = "sdf_zip"
    ZIP = "zip"

    def __str__(self) -> str:
        return str(self.value)
