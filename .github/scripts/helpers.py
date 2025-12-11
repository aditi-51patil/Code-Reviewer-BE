import aiohttp
import random
import asyncio

async def get_git_files(repo_name, pr_number, github_token):
    headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
    try:
        url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/files"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        print(f"Error getting diff from {pr_number} : {e}")
        return {}
async def p(attempt: int, base: float = 1.0, cap: float = 30.0):
    """Exponential backoff with jitter."""
    exp = min(cap, base * (2 ** attempt))
    jitter = random.uniform(0, exp * 0.1)
    await asyncio.sleep(exp + jitter)

async def post_comments_api(repo_name, pr_number, github_token, data, session):
    try:
        url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/reviews"
        headers = {
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json'
                }
        async with session.post(url, headers = headers, json = data) as response:
            if response.status == 422:
                error_text = await response.text()
                print(f"Error posting inline comments: {error_text}")
                return 0
            response.raise_for_status()
            print(f"Posted {len(data['comments'])} inline comment(s) for {data['file_path']}")
            return len(data['comments'])
    except Exception as e:
        print(f"Error posting inline comments for {data['file_path']}: {e}")
        return 0

async def _sleep_with_backoff(attempt: int, base: float = 1.0, cap: float = 30.0):
    """Exponential backoff with jitter."""
    exp = min(cap, base * (2 ** attempt))
    jitter = random.uniform(0, exp * 0.1)
    await asyncio.sleep(exp + jitter)
async def _parse_retry_delay_from_error(exc) -> float:
    try:
        
        if isinstance(exc.args[0],dict):
            d = exc.args[0]
        else:
            d = None
        if d:
            for detail in d.get('error',{}).get('details',[]):
                if detail.get('@type','').endswith('RetryInfo'):
                    retry = detail.get('retryDelay')
                    if isinstance(retry, str) and retry.endswith('s'):
                        return float(retry[:-1])
        import re
        text = str(exc)
        m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", text)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return 0.0
    

rating_emoji = {
            "APPROVE": "✅",
            "REQUEST_CHANGES": "❌",
            "COMMENT": "💭"
        }

severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
type_emoji = {
                    "bug": "🐛",
                    "style": "🎨",
                    "performance": "⚡",
                    "security": "🔒",
                    "maintainability": "🔧"
                }
