from enum import Enum


class Source(str, Enum):
    PRODUCTION = "production"
    TEST = "test"

    def __str__(self) -> str:
        return str(self.value)
