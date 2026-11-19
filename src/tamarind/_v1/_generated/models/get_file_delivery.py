from enum import Enum


class GetFileDelivery(str, Enum):
    INLINE = "inline"
    REDIRECT = "redirect"
    URL = "url"

    def __str__(self) -> str:
        return str(self.value)
