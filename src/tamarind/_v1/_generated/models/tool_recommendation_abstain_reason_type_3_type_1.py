from enum import Enum


class ToolRecommendationAbstainReasonType3Type1(str, Enum):
    CATALOG_NOT_CONFIGURED = "catalog_not_configured"
    CLASSIFICATION_FAILED = "classification_failed"
    NEEDS_MORE_DETAIL = "needs_more_detail"
    NOT_AVAILABLE_TO_YOUR_ACCOUNT = "not_available_to_your_account"
    NOT_A_SUPPORTED_TASK = "not_a_supported_task"
    NO_RECOMMENDATION = "no_recommendation"
    RANKING_FAILED = "ranking_failed"

    def __str__(self) -> str:
        return str(self.value)
