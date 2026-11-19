from enum import Enum


class SubmissionChannel(str, Enum):
    AGENT = "agent"
    API = "api"
    CAMPAIGN_AGENT = "campaign-agent"
    CLI = "cli"
    MCP = "mcp"
    SDK = "sdk"
    WEB = "web"

    def __str__(self) -> str:
        return str(self.value)
