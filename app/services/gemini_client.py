import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
PRODUCT_API_KEY = os.getenv("PRODUCT_API_KEY")
gemini_client = genai.Client(api_key=PRODUCT_API_KEY)