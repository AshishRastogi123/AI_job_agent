#!/usr/bin/env python3
"""
Database initialization script using SQLAlchemy ORM
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import engine
from db.models import Base
from utils.logging_config import get_logger

logger = get_logger(__name__)


def init_database():
    """Initialize database with schema using SQLAlchemy"""
    try:
        logger.info("Initializing database schema...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database initialized successfully!")
        logger.info("Next step: Run 'python seed_demo.py' to add demo data.")
    
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error("Make sure PostgreSQL is running and DB_URL is configured correctly in .env")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
