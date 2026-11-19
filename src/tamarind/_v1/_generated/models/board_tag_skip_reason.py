from enum import Enum


class BoardTagSkipReason(str, Enum):
    ALREADY_TAGGED = "already-tagged"
    CHILD_JOB = "child-job"
    FAILED = "failed"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not-found"
    PROJECT_POLICY = "project-policy"
    UNSUPPORTED_TYPE = "unsupported-type"

    def __str__(self) -> str:
        return str(self.value)
