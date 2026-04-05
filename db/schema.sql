-- Database schema for AI Job Application Agent
-- PostgreSQL

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    resume_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work experience table
CREATE TABLE work_experience (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    company VARCHAR(255) NOT NULL,
    position VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Education table
CREATE TABLE education (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    institution VARCHAR(255) NOT NULL,
    degree VARCHAR(255) NOT NULL,
    field_of_study VARCHAR(255),
    start_date DATE,
    end_date DATE,
    gpa DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills table
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    skill_name VARCHAR(255) NOT NULL,
    proficiency_level VARCHAR(50), -- e.g., Beginner, Intermediate, Expert
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, skill_name)
);

-- Custom answers table (key-value store for dynamic fields)
CREATE TABLE custom_answers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    field_key VARCHAR(255) NOT NULL,
    field_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, field_key)
);

-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    company VARCHAR(255),
    title VARCHAR(255),
    ats_platform VARCHAR(100), -- e.g., Workday, Greenhouse, Lever, LinkedIn
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, applied, failed
    applied_at TIMESTAMP,
    failure_reason TEXT,
    unanswered_fields JSONB, -- Store as JSON for flexibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_work_experience_user_id ON work_experience(user_id);
CREATE INDEX idx_education_user_id ON education(user_id);
CREATE INDEX idx_skills_user_id ON skills(user_id);
CREATE INDEX idx_custom_answers_user_id ON custom_answers(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_ats_platform ON jobs(ats_platform);