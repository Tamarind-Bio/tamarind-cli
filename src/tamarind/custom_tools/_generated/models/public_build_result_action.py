from enum import Enum


class PublicBuildResultAction(str, Enum):
    BUILD = "build"
    REUSE_IMAGE = "reuse_image"
    UNCHANGED = "unchanged"

    def __str__(self) -> str:
        return str(self.value)
