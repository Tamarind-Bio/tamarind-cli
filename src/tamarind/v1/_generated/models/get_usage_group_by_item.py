from enum import Enum


class GetUsageGroupByItem(str, Enum):
    AGENT = "agent"
    APIKEY = "apiKey"
    CAMPAIGNMODE = "campaignMode"
    CUSTOMTOOL = "customTool"
    DAY = "day"
    GPU = "gpu"
    MODEL = "model"
    MONTH = "month"
    PIPELINE = "pipeline"
    PROJECT = "project"
    SOURCE = "source"
    TEAM = "team"
    TOOL = "tool"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
