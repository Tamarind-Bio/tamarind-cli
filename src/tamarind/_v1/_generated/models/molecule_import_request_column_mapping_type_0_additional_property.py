from enum import Enum


class MoleculeImportRequestColumnMappingType0AdditionalProperty(str, Enum):
    IGNORE = "ignore"
    NAME = "name"
    NOTES = "notes"
    SMILES = "smiles"
    TAG = "tag"

    def __str__(self) -> str:
        return str(self.value)
