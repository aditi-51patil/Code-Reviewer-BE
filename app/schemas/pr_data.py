from pydantic import BaseModel

class PRData(BaseModel):
    pr_title: str
    pr_body: str
    author: str
    diff: str
    owner: str
    pull_number: str
    repo_name: str
    commit_id: str
