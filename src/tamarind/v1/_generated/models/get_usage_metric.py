from enum import Enum


class GetUsageMetric(str, Enum):
    DOLLARS = "dollars"
    HOURS = "hours"
    JOBS = "jobs"
    LLMCOST = "llmCost"
    LLMTOKENS = "llmTokens"
    WEIGHTEDHOURS = "weightedHours"

    def __str__(self) -> str:
        return str(self.value)
