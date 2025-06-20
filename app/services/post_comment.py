from app.constants.constants import create_comment_api_path
from app.api_helper.api_helper import APIHelper
from app.schemas.PostCommentBody import PostCommentBody


def post_comment(payload: PostCommentBody, repo, owner, pull_number):
    post_comment_url = create_comment_api_path(owner, repo, pull_number)
    apihelper = APIHelper()
    apihelper.post_request(post_comment_url, payload)
