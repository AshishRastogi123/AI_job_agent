#!/usr/bin/env python3
"""
Custom Data Seeder for AI Job Application Agent
Uses REAL candidate data (Ashish Rastogi)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_session
from db.models import User, WorkExperience, Education, Skill, CustomAnswer, Job
from datetime import datetime, timedelta
from utils.logging_config import get_logger

logger = get_logger(__name__)


def seed_real_data():
    session = get_session()

    try:
        # Remove old demo user
        session.query(User).filter(User.email == "demo@example.com").delete()
        session.commit()

        # Create REAL user
        user = User(
            name="Ashish Kumar Rastogi",
            email="rastogiashish835@gmail.com",
            phone="+91 8445631880",
            resume_path="resumes/resume_unknown_20260408.pdf"
        )
        session.add(user)
        session.flush()
        user_id = user.id

        logger.info(f"✅ Created REAL user: {user.name}")

        # ========================
        # EXPERIENCE
        # ========================
        experiences = [
            {
                'company': 'PearlThoughts',
                'position': 'AI Engineer Intern',
                'start_date': datetime(2026, 1, 1),
                'end_date': datetime(2026, 2, 1),
                'description': 'Worked on ERPNext Accounts module modernization and Python code refactoring.'
            },
            {
                'company': 'EduSkills (Google Supported)',
                'position': 'AI/ML Intern',
                'start_date': datetime(2025, 7, 1),
                'end_date': datetime(2025, 9, 1),
                'description': 'Developed CNN models for image classification using TensorFlow.'
            }
        ]

        for exp in experiences:
            session.add(WorkExperience(
                user_id=user_id,
                company=exp['company'],
                position=exp['position'],
                start_date=exp['start_date'].date(),
                end_date=exp['end_date'].date(),
                description=exp['description']
            ))

        # ========================
        # EDUCATION
        # ========================
        education = [
    {
        'institution': 'Invertis University',
        'degree': 'Master of Computer Applications',
        'field_of_study': 'Computer Applications',
        'start_date': datetime(2024, 1, 1),
        'end_date': datetime(2026, 12, 31),
        'gpa': None
    },
    {
        'institution': 'MJPRU',
        'degree': 'Bachelor of Science',
        'field_of_study': 'Science',
        'start_date': datetime(2021, 1, 1),
        'end_date': datetime(2024, 1, 1),
        'gpa': 7.78   # ✅ FIXED (77.8% → 7.78 GPA)
    }
]

        for edu in education:
            session.add(Education(
                user_id=user_id,
                institution=edu['institution'],
                degree=edu['degree'],
                field_of_study=edu['field_of_study'],
                start_date=edu['start_date'].date(),
                end_date=edu['end_date'].date(),
                gpa=edu['gpa']
            ))

        # ========================
        # SKILLS
        # ========================
        skills = [
            "Python", "C++", "JavaScript",
            "Machine Learning", "Deep Learning",
            "TensorFlow", "PyTorch", "OpenCV",
            "Flask", "Node.js",
            "MongoDB", "MySQL",
            "Git", "REST APIs"
        ]

        for skill in skills:
            session.add(Skill(
                user_id=user_id,
                skill_name=skill,
                proficiency_level="Intermediate"
            ))

        # ========================
        # CUSTOM ANSWERS (IMPORTANT 🔥)
        # ========================
        custom_answers = [
            ('linkedin_url', 'https://linkedin.com/in/ashish-rastogi-77153331a'),
            ('github_url', 'https://github.com/AshishRastogi123'),
            ('location', 'Bareilly, Uttar Pradesh, India'),
            ('city', 'Bareilly'),
            ('state', 'Uttar Pradesh'),
            ('country', 'India'),
            ('zip_code', '243001'),
            ('address', 'Bareilly, Uttar Pradesh'),
            ('gender', 'Male'),
            ('hispanic', 'No'),
            ('veteran', 'Not a veteran'),
            ('disability', 'No disability'),
            ('degree', 'Master of Computer Applications'),
            ('availability', 'Immediate'),
            ('work_authorization', 'Authorized to work in India')
        ]

        for key, value in custom_answers:
            session.add(CustomAnswer(
                user_id=user_id,
                field_key=key,
                field_value=value
            ))

        # ========================
        # JOBS (optional)
        # ========================
        session.query(Job).delete()

        jobs = [
            {
                'url': 'https://job-boards.greenhouse.io/studycontractors/jobs/4772776008',
                'company': 'Study.com',
                'title': 'Practice Test Writer',
                'ats_platform': 'greenhouse'
            }
        ]

        for job_data in jobs:
            session.add(Job(
                url=job_data['url'],
                company=job_data['company'],
                title=job_data['title'],
                ats_platform=job_data['ats_platform'],
                status='pending'
            ))

        # ========================
        # COMMIT
        # ========================
        session.commit()

        logger.info("\n" + "="*50)
        logger.info("🚀 REAL DATA SEEDED SUCCESSFULLY")
        logger.info("="*50)
        logger.info(f"User: {user.name}")
        logger.info(f"Email: {user.email}")
        logger.info("\nRun agent:")
        logger.info(f"python main.py --user-id {user_id} --process-queue")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        session.rollback()
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    seed_real_data()