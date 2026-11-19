from enum import Enum


class UpdateProjectNotesBodyStatusesAddItemTone(str, Enum):
    CUSTOM = "custom"
    NEUTRAL = "neutral"
    RED = "red"
    SUCCESS = "success"
    YELLOW = "yellow"

    def __str__(self) -> str:
        return str(self.value)
