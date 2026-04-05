import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_groq import ChatGroq
from config import OPENAI_API

def get_llm():
    return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=OPENAI_API
            )
