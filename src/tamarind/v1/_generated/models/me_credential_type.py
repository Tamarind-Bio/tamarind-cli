from enum import Enum


class MeCredentialType(str, Enum):
    AGENTTRIAL = "agentTrial"
    APIKEY = "apiKey"
    OAUTH = "oauth"
    SESSION = "session"

    def __str__(self) -> str:
        return str(self.value)
