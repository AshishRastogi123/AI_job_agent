#!/usr/bin/env python3
"""
Demo Data Seeder for AI Job Application Agent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_connection
from db.queries import insert_job

def seed_demo_data():
    """Seed demo user profile and job URLs"""

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Insert demo user
        cur.execute("""
            INSERT INTO users (name, email, phone, resume_path)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, ('John Doe', 'john.doe@example.com', '+1-555-0123', 'resumes/john_doe.pdf'))

        # Get user ID
        cur.execute("SELECT id FROM users WHERE email = %s", ('john.doe@example.com',))
        user_id = cur.fetchone()[0]

        # Insert work experience
        work_experiences = [
            ('Software Engineer', 'Tech Corp', '2021-06-01', '2024-01-01',
             'Developed web applications using Python and React. Led a team of 3 developers.'),
            ('Junior Developer', 'Startup Inc', '2019-01-01', '2021-05-31',
             'Built REST APIs and maintained legacy systems. Improved performance by 40%.')
        ]

        for title, company, start, end, desc in work_experiences:
            cur.execute("""
                INSERT INTO work_experience (user_id, position, company, start_date, end_date, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, title, company, start, end, desc))

        # Insert education
        cur.execute("""
            INSERT INTO education (user_id, institution, degree, field_of_study, start_date, end_date, gpa)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, 'State University', 'Bachelor of Science', 'Computer Science', '2015-09-01', '2019-05-31', 3.8))

        # Insert skills
        skills = [
            ('Python', 'Expert'),
            ('JavaScript', 'Advanced'),
            ('React', 'Advanced'),
            ('SQL', 'Intermediate'),
            ('Docker', 'Intermediate')
        ]

        for skill, level in skills:
            cur.execute("""
                INSERT INTO skills (user_id, skill_name, proficiency_level)
                VALUES (%s, %s, %s)
            """, (user_id, skill, level))

        # Insert custom answers
        custom_answers = [
            ('linkedin_url', 'https://linkedin.com/in/johndoe'),
            ('github_url', 'https://github.com/johndoe'),
            ('portfolio_url', 'https://johndoe.dev'),
            ('location', 'San Francisco, CA'),
            ('visa_status', 'US Citizen')
        ]

        for key, value in custom_answers:
            cur.execute("""
                INSERT INTO custom_answers (user_id, field_key, field_value)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, field_key) DO UPDATE SET field_value = EXCLUDED.field_value
            """, (user_id, key, value))

        # Insert demo job URLs
        demo_jobs = [
            ('https://boards.greenhouse.io/companyxyz/jobs/12345', 'Company XYZ', 'Senior Python Developer', 'greenhouse'),
            ('https://jobs.lever.co/companyabc/67890', 'Company ABC', 'Full Stack Engineer', 'lever'),
            ('https://we.workday.com/companydef/54321', 'Company DEF', 'Software Architect', 'workday'),
            ('https://www.linkedin.com/jobs/view/98765', 'Company GHI', 'DevOps Engineer', 'linkedin'),
            ('https://boards.greenhouse.io/companyjkl/jobs/11223', 'Company JKL', 'Machine Learning Engineer', 'greenhouse'),
            ('https://jobs.lever.co/companymno/44556', 'Company MNO', 'Frontend Developer', 'lever')
        ]

        for url, company, title, ats in demo_jobs:
            insert_job(url, company, title, ats)

        conn.commit()
        print("Demo data seeded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_demo_data()