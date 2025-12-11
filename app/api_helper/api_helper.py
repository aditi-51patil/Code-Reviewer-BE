import requests
from dotenv import load_dotenv
import os

class APIHelper:
    def __init__(self):
        load_dotenv()
        self.GIT_TOKEN = os.getenv('GITHUB_TOKEN')
        self.headers = {
            "Authorization": f"Bearer {self.GIT_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    def post_request(self, url, payload):
        return requests.post(url, headers=self.headers, json=payload)
