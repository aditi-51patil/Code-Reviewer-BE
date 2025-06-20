from pydantic import BaseModel


class PostCommentBody(BaseModel):
    owner: str
    repo: str
    pull_number: str
    body: str
    commit_id: str
    path: str
    headers: object
