from enum import Enum


class PublicGitHubConnectionStatus(str, Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"

    def __str__(self) -> str:
        return str(self.value)
