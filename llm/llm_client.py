from langchain.chat_models import ChatOpenAI
from config import OPENAI_API

def get_llm():
    return ChatOpenAI(
            model="gpt4",
            temperature=0.3,
            openai_api_key=OPENAI_API
            )
