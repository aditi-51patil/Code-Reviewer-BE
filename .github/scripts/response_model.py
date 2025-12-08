from pydantic import BaseModel
from enum_types import RatingEnum, SeverityEnum, IssueTypeEnum
class IssueModel(BaseModel):
    type: IssueTypeEnum
    severity:SeverityEnum
    line:int
    message: str
    suggestion: str

class ResponseSchema(BaseModel):
    overall_rating: RatingEnum
    summary: str
    issues: list[IssueModel]
    positive_feedback: list[str]

