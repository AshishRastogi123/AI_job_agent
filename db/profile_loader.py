from db.queries import get_user
from db.connection import get_connection

def load_profile(user_id):
    conn = get_connection()
    cur = conn.cursor()

    # Get user basic info
    cur.execute("SELECT name, email, phone, resume_path FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return None

    profile = {
        "name": user[0],
        "email": user[1],
        "phone": user[2],
        "resume_path": user[3],
        "work_experience": [],
        "education": [],
        "skills": [],
        "custom_answers": {}
    }

    # Get work experience
    cur.execute("""
        SELECT company, position, start_date, end_date, description
        FROM work_experience
        WHERE user_id = %s
        ORDER BY start_date DESC
    """, (user_id,))
    for exp in cur.fetchall():
        profile["work_experience"].append({
            "company": exp[0],
            "position": exp[1],
            "start_date": str(exp[2]),
            "end_date": str(exp[3]) if exp[3] else "Present",
            "description": exp[4]
        })

    # Get education
    cur.execute("""
        SELECT institution, degree, field_of_study, start_date, end_date, gpa
        FROM education
        WHERE user_id = %s
        ORDER BY start_date DESC
    """, (user_id,))
    for edu in cur.fetchall():
        profile["education"].append({
            "institution": edu[0],
            "degree": edu[1],
            "field_of_study": edu[2],
            "start_date": str(edu[3]) if edu[3] else None,
            "end_date": str(edu[4]) if edu[4] else None,
            "gpa": float(edu[5]) if edu[5] else None
        })

    # Get skills
    cur.execute("SELECT skill_name, proficiency_level FROM skills WHERE user_id = %s", (user_id,))
    for skill in cur.fetchall():
        profile["skills"].append({
            "name": skill[0],
            "proficiency": skill[1]
        })

    # Get custom answers
    cur.execute("SELECT field_key, field_value FROM custom_answers WHERE user_id = %s", (user_id,))
    for answer in cur.fetchall():
        profile["custom_answers"][answer[0]] = answer[1]

    conn.close()
    return profile