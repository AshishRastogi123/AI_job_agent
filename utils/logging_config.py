"""
Logging configuration for AI Job Application Agent
"""

import logging
import logging.handlers
import os
from config import LOG_LEVEL, LOG_FILE, DEBUG

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Create logger
logger = logging.getLogger('job_agent')
logger.setLevel(LOG_LEVEL)

# File handler
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL if DEBUG else logging.INFO)
console_formatter = logging.Formatter(
    '%(levelname)s - [%(name)s] - %(message)s'
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Configure other loggers
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('playwright').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
