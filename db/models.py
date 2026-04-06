"""
SQLAlchemy database models for AI Job Application Agent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Numeric, JSON, func, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User/Candidate profile"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    resume_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    custom_answers = relationship("CustomAnswer", back_populates="user", cascade="all, delete-orphan")


class WorkExperience(Base):
    """Work experience entry"""
    __tablename__ = "work_experience"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="work_experiences")
    
    __table_args__ = (
        Index("idx_work_experience_user_id", user_id),
    )


class Education(Base):
    """Education entry"""
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)
    gpa = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="education")
    
    __table_args__ = (
        Index("idx_education_user_id", user_id),
    )


class Skill(Base):
    """Skills entry"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    proficiency_level = Column(String(50))  # Beginner, Intermediate, Expert, Advanced
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="skills")
    
    __table_args__ = (
        UniqueConstraint("user_id", "skill_name", name="uq_user_skill"),
        Index("idx_skills_user_id", user_id),
    )


class CustomAnswer(Base):
    """Custom answers (key-value store for dynamic fields)"""
    __tablename__ = "custom_answers"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    field_key = Column(String(255), nullable=False)
    field_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="custom_answers")
    
    __table_args__ = (
        UniqueConstraint("user_id", "field_key", name="uq_user_field_key"),
        Index("idx_custom_answers_user_id", user_id),
    )


class Job(Base):
    """Job application tracking"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    url = Column(Text, nullable=False, unique=True)
    company = Column(String(255))
    title = Column(String(255))
    ats_platform = Column(String(100))  # workday, greenhouse, lever, linkedin, etc.
    status = Column(String(50), default="pending")  # pending, processing, applied, failed, backlog
    applied_at = Column(DateTime)
    failure_reason = Column(Text)
    unanswered_fields = Column(JSON)  # Store as JSON for flexibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_jobs_status", status),
        Index("idx_jobs_ats_platform", ats_platform),
    )


class ApplicationLog(Base):
    """Application log for tracking and debugging"""
    __tablename__ = "application_logs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    step = Column(String(100), nullable=False)  # fetch, extract_jd, generate_resume, etc.
    status = Column(String(50), nullable=False)  # success, failure
    message = Column(Text)
    error_details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_application_logs_job_id", job_id),
        Index("idx_application_logs_user_id", user_id),
    )
