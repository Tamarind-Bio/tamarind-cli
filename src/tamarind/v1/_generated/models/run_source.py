from enum import Enum


class RunSource(str, Enum):
    PRODUCTION = "production"
    TEST = "test"

    def __str__(self) -> str:
        return str(self.value)
