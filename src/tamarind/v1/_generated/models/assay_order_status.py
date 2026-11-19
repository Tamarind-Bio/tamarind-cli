from enum import Enum


class AssayOrderStatus(str, Enum):
    APPROVED = "approved"
    CANCELLED = "cancelled"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    PENDING_QUOTE = "pending_quote"
    REJECTED = "rejected"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
