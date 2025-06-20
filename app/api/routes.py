from fastapi import APIRouter
from app.schemas.pr_data import PRData
from app.services.gemini import review_code_with_gemini

router = APIRouter()


@router.post("/review")
async def review(data: PRData):
    return review_code_with_gemini(data)

#
# prompt = PRData(pr_title="CRG-245 Created a program to create subsequence of string",
#                 pr_body="This is the first commit",
#                 author="Aditi Patil",
#                 owner="Aditi Patil",
#                 pull_number="123",
#                 repo_name="HackerEarth-Solutions-Python-CodeMonk",
#                 diff="""
#         class Solution:
#         def isSubsequence(self, s: str, t: str) -> bool:
#             if len(s) == 0:
#                 return True
#             i,j = 0, 0
#             t = t[:]
#             while  i < len(s) and j < len(t):
#                 if s[i] == t[j]:
#                     i += 1
#                 if i>= len(s):
#                     return True
#                 j += 1
#             return False
#
# """)
#
# review_code_with_gemini(prompt)
