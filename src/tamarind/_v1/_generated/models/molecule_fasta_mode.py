from enum import Enum


class MoleculeFastaMode(str, Enum):
    ONE_ENTITY_PER_FILE = "one-entity-per-file"
    ONE_ENTITY_PER_HEADER = "one-entity-per-header"

    def __str__(self) -> str:
        return str(self.value)
