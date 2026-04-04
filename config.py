import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("DB_URL")