import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY").strip()
)