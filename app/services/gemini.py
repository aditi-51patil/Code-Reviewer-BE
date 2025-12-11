from google.genai import types
from app.schemas.response_data import ResponseSchema
from app.services.gemini_client import gemini_client
from app.services.post_comment import post_comment
from app.schemas.PostCommentBody import PostCommentBody


def review_code_with_gemini(prompt):
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction="""
            You are senior software engineer.  \
            Your job is used to provide code reviews in a structured manner along \
            with line numbers and suggestions""",
            response_mime_type="application/json",
            response_schema=ResponseSchema
        ),
        contents=f"""
                PR Title: {prompt.pr_title}
                Author: {prompt.author}
                Description: {prompt.pr_body}
                
                --- Code ---
                {prompt.diff}
    
                """
    )
    for comment in response.text.review:
        post_comment(PostCommentBody(
            owner=prompt.owner,
            repo=prompt.repo_name,
            pull_number=prompt.pull_number,
            body=prompt.comment,
            commit_id=prompt.commit_id,
            path=comment.file_name,
            headers={
                'X-GitHub-Api-Version': '2022-11-28',
                'accept': 'application/vnd.github+json'
            }
        ), prompt.repo_name, prompt.author, prompt.pull_number)
