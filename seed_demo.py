#!/usr/bin/env python3
"""
Demo Data Seeder for AI Job Application Agent
Creates realistic test data with candidate profile and sample jobs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_session
from db.models import User, WorkExperience, Education, Skill, CustomAnswer, Job
from datetime import datetime, timedelta
from utils.logging_config import get_logger

logger = get_logger(__name__)


def seed_demo_data():
    """Seed comprehensive demo data"""
    session = get_session()
    
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == "demo@example.com").first()
        if existing_user:
            logger.info(f"User already exists with ID: {existing_user.id}")
            user_id = existing_user.id
            # Clear old data
            session.query(WorkExperience).filter(WorkExperience.user_id == user_id).delete()
            session.query(Education).filter(Education.user_id == user_id).delete()
            session.query(Skill).filter(Skill.user_id == user_id).delete()
            session.commit()
        else:
            # Create new user
            user = User(
                name="Alex Johnson",
                email="demo@example.com",
                phone="+1-555-0123",
                resume_path="resumes/demo_resume.pdf"
            )
            session.add(user)
            session.flush()
            user_id = user.id
            logger.info(f"✅ Created user with ID: {user_id}")
        
        # Add work experience (3-4 years)
        experiences = [
            {
                'company': 'Tech Innovations Inc.',
                'position': 'Senior Software Engineer',
                'start_date': datetime.now() - timedelta(days=365),
                'end_date': datetime.now(),
                'description': 'Led development of microservices architecture using Python and Kubernetes. '
                               'Improved system performance by 40% through optimization and caching strategies. '
                               'Mentored 3 junior developers and established code review standards.'
            },
            {
                'company': 'Data Systems Corp',
                'position': 'Software Engineer',
                'start_date': datetime.now() - timedelta(days=730),
                'end_date': datetime.now() - timedelta(days=365),
                'description': 'Developed RESTful APIs for data processing pipelines. '
                               'Implemented MongoDB database solutions and improved query performance by 60%. '
                               'Worked with cross-functional teams to deliver features on schedule.'
            },
            {
                'company': 'WebFlow Solutions',
                'position': 'Junior Developer',
                'start_date': datetime.now() - timedelta(days=1095),
                'end_date': datetime.now() - timedelta(days=730),
                'description': 'Built full-stack web applications using React and Node.js. '
                               'Implemented automated testing and CI/CD pipelines. '
                               'Participated in agile development process with 2-week sprints.'
            }
        ]
        
        for exp in experiences:
            work_exp = WorkExperience(
                user_id=user_id,
                company=exp['company'],
                position=exp['position'],
                start_date=exp['start_date'].date(),
                end_date=exp['end_date'].date() if exp.get('end_date') else None,
                description=exp['description']
            )
            session.add(work_exp)
        
        logger.info("✅ Added 3 work experiences")
        
        # Add education
        education = [
            {
                'institution': 'State University',
                'degree': 'Master of Science',
                'field_of_study': 'Computer Science',
                'start_date': datetime.now() - timedelta(days=1460),
                'end_date': datetime.now() - timedelta(days=1095),
                'gpa': 3.8
            },
            {
                'institution': 'Tech Institute',
                'degree': 'Bachelor of Science',
                'field_of_study': 'Computer Engineering',
                'start_date': datetime.now() - timedelta(days=2920),
                'end_date': datetime.now() - timedelta(days=1460),
                'gpa': 3.6
            }
        ]
        
        for edu in education:
            education_record = Education(
                user_id=user_id,
                institution=edu['institution'],
                degree=edu['degree'],
                field_of_study=edu['field_of_study'],
                start_date=edu['start_date'].date(),
                end_date=edu['end_date'].date(),
                gpa=edu['gpa']
            )
            session.add(education_record)
        
        logger.info("✅ Added 2 education records")
        
        # Add skills
        skills = [
            ('Python', 'Expert'),
            ('JavaScript', 'Advanced'),
            ('Java', 'Advanced'),
            ('SQL', 'Advanced'),
            ('Docker', 'Advanced'),
            ('Kubernetes', 'Intermediate'),
            ('AWS', 'Intermediate'),
            ('React', 'Advanced'),
            ('Node.js', 'Advanced'),
            ('PostgreSQL', 'Advanced'),
            ('MongoDB', 'Intermediate'),
            ('Git', 'Expert'),
            ('Linux', 'Intermediate'),
            ('CI/CD', 'Intermediate'),
            ('Agile', 'Advanced'),
        ]
        
        for skill_name, proficiency in skills:
            skill = Skill(
                user_id=user_id,
                skill_name=skill_name,
                proficiency_level=proficiency
            )
            session.add(skill)
        
        logger.info(f"✅ Added {len(skills)} skills")
        
        # Add custom answers
        custom_answers = [
            ('linkedin_url', 'https://linkedin.com/in/alexjohnson'),
            ('github_url', 'https://github.com/alexjohnson'),
            ('personal_website', 'https://alexjohnson.dev'),
            ('location', 'San Francisco, CA'),
            ('availability', '2 weeks notice'),
            ('visa_sponsorship', 'Not required - US Citizen'),
            ('work_authorization', 'Authorized to work in US'),
            ('security_clearance', 'None'),
            ('willing_to_relocate', 'Open to discussion'),
        ]
        
        for key, value in custom_answers:
            custom_answer = CustomAnswer(
                user_id=user_id,
                field_key=key,
                field_value=value
            )
            session.add(custom_answer)
        
        logger.info(f"✅ Added {len(custom_answers)} custom answers")
        
        # Add demo jobs across different ATS platforms
        demo_jobs = [
            {
                'url': 'https://boards.greenhouse.io/techcompany/jobs/4234512',
                'company': 'TechCorp',
                'title': 'Senior Full Stack Engineer',
                'ats_platform': 'greenhouse'
            },
            {
                'url': 'https://techcompany.wd5.myworkdayjobs.com/en-US/search/job/sr-software-engineer',
                'company': 'MegaTech Inc',
                'title': 'Sr. Software Engineer',
                'ats_platform': 'workday'
            },
            {
                'url': 'https://jobs.lever.co/startup123/lead-backend-engineer',
                'company': 'StartupXYZ',
                'title': 'Lead Backend Engineer',
                'ats_platform': 'lever'
            },
            {
                'url': 'https://anothertech.greenhouse.io/jobs/7654321',
                'company': 'AnotherTech',
                'title': 'Platform Engineer',
                'ats_platform': 'greenhouse'
            },
            {
                'url': 'https://global.wd5.myworkdayjobs.com/jobs/python-engineer',
                'company': 'Global Systems',
                'title': 'Python Engineer',
                'ats_platform': 'workday'
            },
            {
                'url': 'https://jobs.lever.co/scaleup/infrastructure-engineer',
                'company': 'ScaleUp Labs',
                'title': 'Infrastructure Engineer',
                'ats_platform': 'lever'
            }
        ]
        
        # Clear existing jobs
        session.query(Job).delete()
        
        for job_data in demo_jobs:
            job = Job(
                url=job_data['url'],
                company=job_data['company'],
                title=job_data['title'],
                ats_platform=job_data.get('ats_platform'),
                status='pending'
            )
            session.add(job)
        
        logger.info(f"✅ Added {len(demo_jobs)} demo job listings")
        
        # Commit all changes
        session.commit()
        
        logger.info("\n" + "="*60)
        logger.info("🚀 Demo data seeded successfully!")
        logger.info("="*60)
        logger.info(f"User ID: {user_id}")
        logger.info(f"Name: Alex Johnson")
        logger.info(f"Email: demo@example.com")
        logger.info(f"Jobs added: {len(demo_jobs)}")
        logger.info("\nYou can now run the agent:")
        logger.info(f"  python main.py --user-id {user_id} --process-queue")
        logger.info("="*60 + "\n")

    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}", exc_info=True)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    seed_demo_data()
