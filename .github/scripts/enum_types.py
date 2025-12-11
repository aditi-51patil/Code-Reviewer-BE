from enum import Enum

class RatingEnum(str, Enum):
    APPROVE= "APPROVE"
    REQUEST_CHANGES= "REQUEST_CHANGES"
    COMMENT= "COMMENT"

class IssueTypeEnum(str, Enum):
    BUG = "bug"
    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"

class SeverityEnum(str,Enum):
    HIGH = 'high'
    LOW = "low"
    MEDIUM = 'medium'