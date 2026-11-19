from enum import Enum


class BatchSourceFormat(str, Enum):
    AUTO = "auto"
    CSV = "csv"
    FASTA = "fasta"
    JSONL = "jsonl"

    def __str__(self) -> str:
        return str(self.value)
