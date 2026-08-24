from enum import Enum


class PublicCustomToolGputype(str, Enum):
    A10 = "A10"
    A100 = "A100"
    L4 = "L4"
    L40S = "L40S"
    NONE = "None"
    T4 = "T4"

    def __str__(self) -> str:
        return str(self.value)
