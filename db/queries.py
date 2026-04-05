from db.connection import get_connection
import json

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def insert_job(url, company=None, title=None, ats_platform=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (url, company, title, ats_platform)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (url, company, title, ats_platform))
    job_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return job_id

def update_job_status(job_id, status, failure_reason=None, unanswered_fields=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs
        SET status = %s, failure_reason = %s, unanswered_fields = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (status, failure_reason, json.dumps(unanswered_fields) if unanswered_fields else None, job_id))
    conn.commit()
    conn.close()

def mark_job_applied(job_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs
        SET status = 'applied', applied_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (job_id,))
    conn.commit()
    conn.close()

def get_pending_jobs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, url FROM jobs WHERE status = 'pending' ORDER BY created_at ASC")
    jobs = cur.fetchall()
    conn.close()
    return jobs

def save_custom_answer(user_id, field_key, field_value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO custom_answers (user_id, field_key, field_value)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, field_key) DO UPDATE SET field_value = EXCLUDED.field_value
    """, (user_id, field_key, field_value))
    conn.commit()
    conn.close()