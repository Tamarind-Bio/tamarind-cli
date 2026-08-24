from enum import Enum


class PublicCustomToolMemory(str, Enum):
    VALUE_0 = "8Gi"
    VALUE_1 = "12Gi"
    VALUE_2 = "24Gi"
    VALUE_3 = "32Gi"
    VALUE_4 = "48Gi"
    VALUE_5 = "64Gi"
    VALUE_6 = "90Gi"
    VALUE_7 = "96Gi"
    VALUE_8 = "180Gi"

    def __str__(self) -> str:
        return str(self.value)
