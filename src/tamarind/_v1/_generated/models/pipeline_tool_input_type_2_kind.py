from enum import Enum


class PipelineToolInputType2Kind(str, Enum):
    PICKERCOMPLEX = "pickerComplex"

    def __str__(self) -> str:
        return str(self.value)
