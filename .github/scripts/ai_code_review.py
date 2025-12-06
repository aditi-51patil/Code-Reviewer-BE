"""
AI Code Review Script for GitHub Actions
This script analyzes changed files in a PR and provides AI-powered code review comments.
"""
from  code_review_with_gemini import CodeReviewWithGemini  
import sys
import asyncio

async def  main():
    try:
        reviewer = CodeReviewWithGemini()
        await reviewer.run_review()
    except Exception as e:
        print(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())