"""
Database query functions using SQLAlchemy ORM
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_session
from db.models import User, Job, CustomAnswer, WorkExperience, Education, Skill, ApplicationLog
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# ==================== User Queries ====================

def get_user(user_id: int) -> User:
    """Get user by ID"""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return user
    finally:
        session.close()


def get_user_profile(user_id: int) -> dict:
    """Get complete user profile with all data"""
    print(f"[DB DEBUG] Querying user profile for user_id={user_id}")
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"[DB DEBUG] No user found for user_id={user_id}")
            return None
        
        profile = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "resume_path": user.resume_path,
            "work_experience": [
                {
                    "company": exp.company,
                    "position": exp.position,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "description": exp.description
                }
                for exp in user.work_experiences
            ],
            "education": [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "start_date": edu.start_date.isoformat() if edu.start_date else None,
                    "end_date": edu.end_date.isoformat() if edu.end_date else None,
                    "gpa": float(edu.gpa) if edu.gpa else None
                }
                for edu in user.education
            ],
            "skills": [
                {
                    "skill_name": skill.skill_name,
                    "proficiency_level": skill.proficiency_level
                }
                for skill in user.skills
            ],
            "custom_answers": {
                answer.field_key: answer.field_value
                for answer in user.custom_answers
            }
        }
        print(f"[DB DEBUG] Loaded profile for user_id={user.id}, email={user.email}")
        return profile
    finally:
        session.close()


def get_last_user_profile() -> dict:
    """Get the most recently created user profile"""
    print("[DB DEBUG] Querying last saved user profile")
    session = get_session()
    """Get the most recently created user profile"""
    session = get_session()
    try:
        user = session.query(User).order_by(User.id.desc()).first()
        if not user:
            return None

        profile = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "resume_path": user.resume_path,
            "work_experience": [
                {
                    "company": exp.company,
                    "position": exp.position,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "description": exp.description
                }
                for exp in user.work_experiences
            ],
            "education": [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "start_date": edu.start_date.isoformat() if edu.start_date else None,
                    "end_date": edu.end_date.isoformat() if edu.end_date else None,
                    "gpa": float(edu.gpa) if edu.gpa else None
                }
                for edu in user.education
            ],
            "skills": [
                {
                    "skill_name": skill.skill_name,
                    "proficiency_level": skill.proficiency_level
                }
                for skill in user.skills
            ],
            "custom_answers": {
                answer.field_key: answer.field_value
                for answer in user.custom_answers
            }
        }
        print(f"[DB DEBUG] Loaded last saved profile for user_id={user.id}, email={user.email}")
        return profile
    finally:
        session.close()


def create_user(name: str, email: str, phone: str = None, resume_path: str = None) -> int:
    """Create new user, return user_id"""
    session = get_session()
    try:
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            logger.info(f"User with email {email} already exists")
            return existing.id
        
        user = User(name=name, email=email, phone=phone, resume_path=resume_path)
        session.add(user)
        session.commit()
        user_id = user.id
        logger.info(f"Created user {user_id}: {name}")
        return user_id
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create user: {e}")
        raise
    finally:
        session.close()


# ==================== Custom Answer Queries ====================

def get_custom_answer(user_id: int, field_key: str) -> str:
    """Get custom answer for a field"""
    session = get_session()
    try:
        answer = session.query(CustomAnswer).filter(
            CustomAnswer.user_id == user_id,
            CustomAnswer.field_key == field_key
        ).first()
        return answer.field_value if answer else None
    finally:
        session.close()


def get_all_custom_answers(user_id: int) -> dict:
    """Get all custom answers for user"""
    session = get_session()
    try:
        answers = session.query(CustomAnswer).filter(CustomAnswer.user_id == user_id).all()
        return {a.field_key: a.field_value for a in answers}
    finally:
        session.close()


def save_custom_answer(user_id: int, field_key: str, field_value: str):
    """Save or update custom answer"""
    session = get_session()
    try:
        answer = session.query(CustomAnswer).filter(
            CustomAnswer.user_id == user_id,
            CustomAnswer.field_key == field_key
        ).first()
        
        if answer:
            answer.field_value = field_value
        else:
            answer = CustomAnswer(user_id=user_id, field_key=field_key, field_value=field_value)
            session.add(answer)
        
        session.commit()
        logger.info(f"Saved custom answer: {field_key} for user {user_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save custom answer: {e}")
        raise
    finally:
        session.close()


# ==================== Job Queries ====================

def insert_job(url: str, company: str = None, title: str = None, ats_platform: str = None) -> int:
    """Insert new job, return job_id"""
    session = get_session()
    try:
        job = Job(url=url, company=company, title=title, ats_platform=ats_platform)
        session.add(job)
        session.commit()
        job_id = job.id
        logger.info(f"Created job {job_id}: {company} - {title}")
        return job_id
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert job: {e}")
        raise
    finally:
        session.close()


def get_pending_jobs(limit: int = 10):
    """Get pending jobs"""
    session = get_session()
    try:
        jobs = session.query(Job).filter(Job.status == "pending").limit(limit).all()
        return [(job.id, job.url) for job in jobs]
    finally:
        session.close()


def get_backlog_jobs(user_id: int):
    """Get jobs in backlog (needs HITL response)"""
    session = get_session()
    try:
        jobs = session.query(Job).filter(Job.status == "backlog").all()
        return jobs
    finally:
        session.close()


def update_job_status(job_id: int, status: str, failure_reason: str = None, unanswered_fields: list = None):
    """Update job status"""
    session = get_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.failure_reason = failure_reason
            if unanswered_fields:
                job.unanswered_fields = unanswered_fields
            job.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated job {job_id} status to {status}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update job status: {e}")
        raise
    finally:
        session.close()


def update_job_ats_platform(job_id: int, ats_platform: str):
    """Update job ATS platform"""
    session = get_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.ats_platform = ats_platform
            job.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated job {job_id} ATS platform to {ats_platform}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update ATS platform: {e}")
        raise
    finally:
        session.close()


def mark_job_applied(job_id: int):
    """Mark job as applied"""
    session = get_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "applied"
            job.applied_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Marked job {job_id} as applied")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to mark job as applied: {e}")
        raise
    finally:
        session.close()


def save_unanswered_fields(job_id: int, unanswered_fields: list):
    """Save unanswered fields for a job"""
    session = get_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.unanswered_fields = unanswered_fields
            job.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Saved {len(unanswered_fields)} unanswered fields for job {job_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save unanswered fields: {e}")
        raise
    finally:
        session.close()


# ==================== Logging Queries ====================

def log_application_step(job_id: int, user_id: int, step: str, status: str, message: str = None, error_details: dict = None):
    """Log application step"""
    session = get_session()
    try:
        log_entry = ApplicationLog(
            job_id=job_id,
            user_id=user_id,
            step=step,
            status=status,
            message=message,
            error_details=error_details
        )
        session.add(log_entry)
        session.commit()
        logger.debug(f"Logged step {step} for job {job_id}: {status}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to log step: {e}")
    finally:
        session.close()


def get_application_logs(job_id: int) -> list:
    """Get all logs for a job"""
    session = get_session()
    try:
        logs = session.query(ApplicationLog).filter(ApplicationLog.job_id == job_id).all()
        return [
            {
                "step": log.step,
                "status": log.status,
                "message": log.message,
                "error_details": log.error_details,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    finally:
        session.close()