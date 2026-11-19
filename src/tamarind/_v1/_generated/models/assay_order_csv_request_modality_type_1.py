from enum import Enum


class AssayOrderCsvRequestModalityType1(str, Enum):
    ANTIBODY = "antibody"
    PROTEIN = "protein"

    def __str__(self) -> str:
        return str(self.value)
