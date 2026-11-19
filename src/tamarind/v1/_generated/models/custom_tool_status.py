from enum import Enum


class CustomToolStatus(str, Enum):
    BUILDING = "Building"
    DEPLOYED = "Deployed"
    DRAFT = "Draft"

    def __str__(self) -> str:
        return str(self.value)
