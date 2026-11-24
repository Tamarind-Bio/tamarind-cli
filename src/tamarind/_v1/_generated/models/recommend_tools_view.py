from enum import Enum


class RecommendToolsView(str, Enum):
    AGENT = "agent"

    def __str__(self) -> str:
        return str(self.value)
