from enum import Enum


class PublicCustomToolStatus(str, Enum):
    BUILDING = "Building"
    DEPLOYED = "Deployed"
    DRAFT = "Draft"

    def __str__(self) -> str:
        return str(self.value)
