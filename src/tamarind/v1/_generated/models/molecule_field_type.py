from enum import Enum


class MoleculeFieldType(str, Enum):
    BOOLEAN = "boolean"
    CATEGORY = "category"
    CHAIN = "chain"
    FLOAT = "float"
    INTEGER = "integer"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
