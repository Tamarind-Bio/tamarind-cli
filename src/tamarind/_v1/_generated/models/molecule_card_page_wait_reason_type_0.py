from enum import Enum


class MoleculeCardPageWaitReasonType0(str, Enum):
    BUSY = "busy"
    STUCK = "stuck"

    def __str__(self) -> str:
        return str(self.value)
