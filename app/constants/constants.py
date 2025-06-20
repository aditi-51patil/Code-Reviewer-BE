
def create_comment_api_path(owner, repo, pull_number):
    return f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments'
