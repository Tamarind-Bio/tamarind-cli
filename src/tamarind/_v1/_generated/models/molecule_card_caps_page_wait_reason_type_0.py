from enum import Enum


class MoleculeCardCapsPageWaitReasonType0(str, Enum):
    BUSY = "busy"
    STUCK = "stuck"

    def __str__(self) -> str:
        return str(self.value)
