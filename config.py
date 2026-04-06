import os
from dotenv import load_dotenv, find_dotenv

env_path = find_dotenv()

load_dotenv(env_path, override=True)


# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "job_agent_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Construct DB URL
if os.getenv("DB_URL"):
    DB_URL = os.getenv("DB_URL")
else:
    DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Redis (optional)
REDIS_URL = os.getenv("REDIS_URL", "")

# Browser settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # milliseconds

# HITL settings
HITL_TIMEOUT = int(os.getenv("HITL_TIMEOUT", "30"))  # seconds
HITL_ENABLED = os.getenv("HITL_ENABLED", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/job_agent.log")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Application
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)