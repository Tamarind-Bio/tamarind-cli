from enum import Enum


class PipelineToolInputType1Kind(str, Enum):
    SMILES = "smiles"

    def __str__(self) -> str:
        return str(self.value)
