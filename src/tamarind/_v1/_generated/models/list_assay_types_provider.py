from enum import Enum


class ListAssayTypesProvider(str, Enum):
    AALPHA = "aalpha"
    ADAPTYV = "adaptyv"
    GENSCRIPT = "genscript"
    GINKGO = "ginkgo"

    def __str__(self) -> str:
        return str(self.value)
