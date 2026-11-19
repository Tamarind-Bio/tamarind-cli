from enum import Enum


class AssayOrderInlineRequestModalityType2Type1(str, Enum):
    ANTIBODY = "antibody"
    PROTEIN = "protein"

    def __str__(self) -> str:
        return str(self.value)
