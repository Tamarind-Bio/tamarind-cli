from enum import Enum


class RerunJobBodyOnly(str, Enum):
    ALL = "all"
    INCOMPLETE = "incomplete"

    def __str__(self) -> str:
        return str(self.value)
