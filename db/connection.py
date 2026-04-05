import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from config import DB_URL

def get_connection():
    return psycopg2.connect(
         dbname="AshishDB",
        user="postgres",
        password="ashish@123",   # your real password
        host="localhost",
        port="5432"
    )
    