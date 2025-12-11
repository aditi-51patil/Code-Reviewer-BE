import os
from google import genai
from google.genai import types
from helpers import get_git_files, post_comments_api,  rating_emoji, severity_emoji, type_emoji, _parse_retry_delay_from_error, _sleep_with_backoff
from typing import List, Dict, Any
import aiohttp
import asyncio
from response_model import ResponseSchema
class CodeReviewWithGemini:
    def __init__(self):
        self.gemini_client = genai.Client(api_key= os.getenv('PRODUCT_API_KEY'))
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.pr_number = os.getenv('PR_NUMBER')
        self.repo_name = os.getenv('REPO_NAME')
        self.changed_files = os.getenv('CHANGED_FILES', '').split(',')
        self.files_diff = {}
        self.max_concurrent = 1  # tune this
        self._sem = asyncio.Semaphore(self.max_concurrent)

        if not all([self.github_token, self.pr_number, self.repo_name]):
            raise ValueError('Missing required environment variables')
    
    
    async def get_all_file_diff(self)-> dict:
        files = await get_git_files(self.repo_name, self.pr_number, self.github_token)
        file_diff_dict = {}
        for file_info in files:
            filename = file_info['filename']
            file_diff_dict[filename] = file_info.get('patch', '')
        self.files_diff = file_diff_dict  
    def get_file_diff(self, file_path: str) -> str:
        """Get the diff for a specific file from cache"""
        return self.files_diff.get(file_path, '')  
    def get_diff_position(self, diff:str, line_number: int) -> int:
        '''
         Calculate the position in the diff for a given line number.
        GitHub's position is the line number in the diff, not in the file.
        '''
        if not diff or not line_number:
            return None
        lines = diff.split('\n')
        current_new_line = 0
        position = 0
        for i, line in enumerate(lines):
            if line.startswith('@@'):
                import re
                matched = re.search(r'\+(\d+)', line)
                if matched:
                    current_new_line = int(matched.group(1)) - 1
                position = i + 1
                continue
            position = i + 1
            if line.startswith('+'):
                current_new_line += 1
                if current_new_line == line_number:
                    return position
            elif line.startswith(' '):
                current_new_line += 1
        return None
    async def get_pr_commit_id(self, session: aiohttp.ClientSession) -> str:
        """Get the latest commit ID from the PR"""
        try:
            url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.pr_number}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                pr_data = await response.json()
                return pr_data['head']['sha']
                
        except Exception as e:
            print(f"Error getting PR commit ID: {e}")
            return None
    def get_file_content(self, file_path:str)-> str:
        ''' Get the current content of file '''
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path} : {e}")
            return ''   
    async def analyze_code_with_ai(self,file_path: str, file_content: str, diff: str) -> Dict[str, any]:
        max_attempts = 6
        attempt = 0
        """Analyze code using OpenAI API"""
        prompt = f"""
        You are an expert code reviewer. Please review the provided code changes and provide constructive feedback.
        Please provide a code review focusing on:
        1. Code quality and best practices
        2. Potential bugs or issues
        3. Performance considerations
        4. Security concerns
        5. Maintainability and readability

        IMPORTANT: For each issue, Identify the specific line number in the diff where the issue occurs.
        The diff uses the format: @@ -old_line,old_count +new_line,new_count @@
        Lines starting with '+' are additions at the new_line position.
        Lines starting with '-' are deletions.
        Lines starting with ' ' (space) are context.
        Be constructive and specific. If no issues are found, still provide positive feedback.
        """
        async with self._sem:
            while True:
                try:
                    response  = await self.gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f'''
                            File: {file_path}
                                    
                            Diff:
                            {diff}

                            Full file content:
                            {file_content}
                        ''',
                        config= types.GenerateContentConfig(
                            system_instruction=prompt,
                            max_output_tokens=800,
                            temperature=0.0,
                            response_schema=ResponseSchema,
                            response_mime_type="application/json",
                        ),  
                    )
                    print(response.text)
                    return response.text

                except Exception as e:
                    attempt += 1
                    if attempt > max_attempts:
                        print("generate_content failed:", e)
                        return {
                            "overall_rating": "COMMENT",
                            "summary": f"Error during AI analysis: {str(e)}",
                            "issues": [],
                            "positive_feedback": []
                        }
                    retry_delay = await _parse_retry_delay_from_error(e)
                    err_text = str(e).lower()
                    if 'resource_exhausted' in err_text or 'rate_limit' in err_text or 'quota' in err_text or '429' in err_text:
                        print(retry_delay)
                        if retry_delay and retry_delay > 0:
                            print(f"API quota hit; sleeping {retry_delay}s (server suggested)")
                            await asyncio.sleep(retry_delay)
                        else:
                            print(f"API quota/rate limit hit; backoff attempt {attempt}")
                            await _sleep_with_backoff(attempt, base=1.0, cap=30.0)
                        continue

                    # For other transient network errors, use backoff as well
                    if 'timeout' in err_text or 'temporar' in err_text or 'connection' in err_text:
                        await _sleep_with_backoff(attempt, base=0.5, cap=20.0)
                        continue

                    # Otherwise non-transient error: break and return safe fallback
                    print("Non-retryable error from generate_content:", e)
                    return {
                        "overall_rating": "COMMENT",
                        "summary": f"Error during AI analysis: {str(e)}",
                        "issues": [],
                        "positive_feedback": []
                    }
    def format_review_comment(self, file_path:str,analysis:Dict[str,Any]) -> str:
        """Format the AI analysis into a GitHub comment"""
        comment = f"## 🤖 AI Code Review - {file_path}\n\n"
        
        comment += f"**Overall Rating:** {rating_emoji.get(analysis['overall_rating'], '💭')} {analysis['overall_rating']}\n\n"
        # Summary
        if analysis.get('summary'):
            comment += f"**Summary:** {analysis['summary']}\n\n"

        if analysis.get('issues'):
            comment += "### Issues Found:\n"
            for issue in analysis['issues']:
                comment += f"- {severity_emoji.get(issue['severity'], '🟡')} {type_emoji.get(issue['type'], '📝')} **{issue['type'].title()}** ({issue['severity']} severity)\n"
                comment += f"  - **Issue:** {issue['message']}\n"
                if issue.get('suggestion'):
                    comment += f"  - **Suggestion:** {issue['suggestion']}\n"
                comment += "\n"
        
        if analysis.get('positive_feedback'):
            comment += "### Positive Feedback:\n"
            for feedback in analysis['positive_feedback']:
                comment += f"- ✅ {feedback}\n"
            comment += "\n"
        return comment
    async def post_inline_comments(self, session: aiohttp.ClientSession, file_path:str, issues: List[Dict[str, Any]], comment, commit_id) ->int:
        """Post inline comments on specific lines using GitHub Review API"""
        if not issues:
            return 0
        diff = self.get_file_diff(file_path)
        comments = []
        for issue in issues:
            if not issue.get('line'):
                continue

            position = self.get_diff_position(diff, issue['line'])
            if position is None:
                print(f"Could not determine diff position for line {issue['line']} in {file_path}")
                continue
            comments.append({
                'path': file_path,
                'position': position,
                'body': comment
            })
        if not comments:
            return 0
        data = {
                'commit_id': commit_id,
                'event': 'COMMENT',  # Can be 'COMMENT', 'APPROVE', or 'REQUEST_CHANGES'
                'comments': comments
            }
        
        return await post_comments_api(self.repo_name, self.pr_number, self.github_token, data, session)
    async def review_file(self, file_path:str) -> Dict:
        """Review a single file (async)"""
        file_content = self.get_file_content(file_path)
        diff = self.get_file_diff(file_path)
        if not file_content and not diff:
            print(f"Could not get content for {file_path}, skipping")
            return ""
        analysis = await self.analyze_code_with_ai(file_path, file_content, diff)
        comment = self.format_review_comment(file_path, analysis)
        return { 'file_path' : file_path, 'analysis': analysis, 'comment': comment }  
    async def run_review(self):
        """Main method to run the code review (async)"""
        print(f"Starting AI code review for PR #{self.pr_number}")
        print(f"Changed files: {self.changed_files}")
        
        if not self.changed_files or self.changed_files == ['']:
            print("No files to review")
            return
        
        # Filter out empty file paths
        files_to_review = [f.strip() for f in self.changed_files if f.strip()]
        
        if not files_to_review:
            print("No valid files to review")
            return
        
        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            # Get PR commit ID for inline comments
            commit_id = await self.get_pr_commit_id(session)
            if not commit_id:
                print("Could not get commit ID, skipping inline comments")
                return
            
            # Fetch all file diffs once
            print("Fetching all file diffs...")
            await self.get_all_file_diff()
            
            # Review all files concurrently
            review_tasks = [self.review_file(file_path) for file_path in files_to_review]
            all_reviews = await asyncio.gather(*review_tasks, return_exceptions=True)
            
            # Process reviews and post inline comments
            
            for review in all_reviews:
                if isinstance(review, Exception):
                    print(f"Error in review: {review}")
                    continue
                
                if not review:
                    continue
                
                file_path = review['file_path']
                analysis = review['analysis']
                
                # Post inline comments for issues with line numbers
                issues_with_lines = [issue for issue in analysis.get('issues', []) if issue.get('line')]
                
                if issues_with_lines:
                    await self.post_inline_comments(
                        session, file_path, issues_with_lines,  review['comment'], commit_id
                    )