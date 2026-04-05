import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Database
DB_URL = os.getenv("DB_URL")

# Redis (optional)
REDIS_URL = os.getenv("REDIS_URL")

# Browser settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# HITL settings
HITL_TIMEOUT = int(os.getenv("HITL_TIMEOUT", "30"))  # seconds

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")