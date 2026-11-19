from enum import Enum


class CreateProjectRequestScope(str, Enum):
    ORG = "org"
    PERSONAL = "personal"

    def __str__(self) -> str:
        return str(self.value)
