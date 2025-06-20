from pydantic import BaseModel


class ReviewComment(BaseModel):
    comment: str
    file_name: str
    line_number: int


class ResponseSchema(BaseModel):
    review: list[ReviewComment]
