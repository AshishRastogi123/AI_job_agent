#!/usr/bin/env python3
"""
Database initialization script
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_connection

def init_database():
    """Initialize database with schema"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Read and execute schema
        with open('db/schema.sql', 'r') as f:
            schema_sql = f.read()

        cur.execute(schema_sql)
        conn.commit()

        print("✅ Database initialized successfully!")
        print("Run 'python seed_demo.py' to add demo data.")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("Make sure PostgreSQL is running and DB_URL is configured correctly.")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database()