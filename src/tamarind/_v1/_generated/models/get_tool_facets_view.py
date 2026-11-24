from enum import Enum


class GetToolFacetsView(str, Enum):
    AGENT = "agent"

    def __str__(self) -> str:
        return str(self.value)
