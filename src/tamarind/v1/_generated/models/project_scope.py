from enum import Enum


class ProjectScope(str, Enum):
    ORG = "org"
    PERSONAL = "personal"
    SHARED = "shared"

    def __str__(self) -> str:
        return str(self.value)
