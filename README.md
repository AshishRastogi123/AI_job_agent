# AI Job Application Agent

AI-powered autonomous job application agent that tailors resumes, generates cover letters, and applies to jobs end-to-end using browser automation and intelligent form filling.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Setup database
createdb job_agent  # Create PostgreSQL database
python init_db.py   # Initialize schema
python seed_demo.py # Add demo data

# 4. Run agent
python main.py --job-url "https://example.com/job"
```

## 🎯 Overview

This system autonomously:
- Fetches job URLs from a queue
- Extracts job descriptions using browser automation
- Generates tailored resumes and cover letters using LLM
- Detects Applicant Tracking Systems (ATS) platforms
- Intelligently fills out job application forms
- Submits applications automatically
- Logs results and handles failures

## 🧱 Architecture

### Core Components

- **Agent Orchestration** (`agent/`): LangGraph-based workflow management
- **LLM Layer** (`llm/`): Resume/cover letter generation and field inference
- **Browser Automation** (`browser/`): Playwright-based form interaction
- **ATS Detection** (`ats/`): Platform fingerprinting and URL pattern matching
- **Database** (`db/`): PostgreSQL with relational schema
- **Queue** (`queue/`): Redis-based job queue (optional)
- **HITL** (`hitl/`): Human-in-the-loop for uncertain fields
- **Utils** (`utils/`): Field mapping and helper functions

### Data Flow

```
Job URL → Extract JD → Generate Resume/Cover → Detect ATS → Fill Form → Submit → Log
```

## 🏗️ Database Schema

The system uses PostgreSQL with the following tables:

- `users`: Candidate profiles
- `work_experience`: Professional experience
- `education`: Academic background
- `skills`: Technical skills
- `custom_answers`: Extensible key-value store for form fields
- `jobs`: Job applications with status tracking

See `db/schema.sql` for complete schema.

## 📋 Detailed Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (optional, for queue persistence)
- Playwright browsers

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repo>
   cd ai-job-agent
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

3. **Database setup:**
   ```bash
   createdb job_agent
   python init_db.py
   python seed_demo.py
   ```

4. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database URL
   ```

### Configuration

Required environment variables:
- `GROQ_API_KEY`: For LLM services (or `OPENAI_API_KEY`)
- `DB_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis URL (optional)

## 🎮 Usage

### Single Job Application

```bash
python main.py --job-url "https://boards.greenhouse.io/company/jobs/12345"
```

### Add Jobs to Queue

```bash
python main.py --add-jobs "url1" "url2" "url3"
```

### Process Queue

```bash
python main.py --process-queue
```

### Custom User

```bash
python main.py --user-id 2 --job-url "https://example.com/job"
```

## 🔍 ATS Detection Logic

The system detects ATS platforms using:

### URL Pattern Matching
- **Workday**: `workday.com`, `wd*.myworkdayjobs.com`, `we.workday.com`
- **Greenhouse**: `boards.greenhouse.io`, `grnh.se`
- **Lever**: `jobs.lever.co`
- **LinkedIn**: `linkedin.com/jobs`

### DOM Fingerprinting
- Searches for platform-specific CSS classes and scripts
- Workday: `wd-content`, `workday` mentions
- Greenhouse: `gh_embedded`, `greenhouse` mentions
- Lever: `lever-application`, `lever` mentions
- LinkedIn: Job-specific LinkedIn pages

## 📝 Form Field Mapping Logic

Fields are mapped using a 4-tier priority system:

### 1. Profile Database
Direct mapping from candidate profile:
- Name → `users.name`
- Email → `users.email`
- Phone → `users.phone`
- Resume → `users.resume_path`

### 2. Custom Answers
Extensible key-value store for learned responses:
- Stores HITL responses for future use
- Matches field names against stored keys

### 3. LLM Inference
Uses GPT/Groq to generate appropriate responses:
- Analyzes field context and candidate profile
- Generates natural, ATS-friendly responses

### 4. Human-in-the-Loop (HITL)
Fallback for uncertain fields:
- Triggers for sensitive data (SSN, salary, criminal history)
- 30-second timeout for user input
- Saves responses to database for future applications

## 🤖 HITL Behavior

When the system encounters uncertain fields:

1. **Detection**: Fields with low confidence or sensitive keywords
2. **Notification**: Console prompt with field details
3. **Timeout**: 30 seconds for user response
4. **Fallback**: Skip field if no response
5. **Learning**: Save successful responses for future use

## 📊 Logging System

Tracks comprehensive application metrics:

- **Job Status**: `pending` → `processing` → `applied`/`failed`
- **Failure Reasons**: Unanswered fields, submission errors
- **Timestamps**: Created, applied, updated times
- **ATS Platform**: Detected platform for analytics

## ⚖️ Scaling Strategy

### Horizontal Scaling
- **Queue-based**: Redis enables multiple worker instances
- **Stateless Workers**: Each job processed independently
- **Load Balancing**: Distribute across multiple machines

### Database Scaling
- **Connection Pooling**: Psycopg2 connection management
- **Indexing**: Optimized queries for job status and user data
- **Partitioning**: Time-based partitioning for job history

### LLM Optimization
- **Caching**: Store generated resumes/cover letters
- **Batch Processing**: Group similar jobs for efficiency
- **Model Selection**: Use smaller models for field inference

### Browser Management
- **Browser Pooling**: Reuse browser instances
- **Headless Mode**: Reduce resource usage
- **Parallel Processing**: Multiple browsers for different jobs

## 🔒 Security Considerations

- **Credential Management**: Environment variables only
- **No Code Credentials**: All secrets externalized
- **HITL Validation**: Human oversight for sensitive fields
- **Rate Limiting**: Respectful application submission pacing

## 🧪 Testing

Run LLM tests:
```bash
python -m llm.test_llm
```

## 📈 Monitoring

- **Application Metrics**: Success rates, ATS detection accuracy
- **Performance**: Processing time per application
- **Error Tracking**: Failure reasons and patterns
- **Queue Health**: Job backlog and processing rates

## 🤝 Contributing

1. Follow modular architecture
2. Add comprehensive logging
3. Include error handling
4. Update documentation
5. Test with multiple ATS platforms

## 📄 License

MIT License - see LICENSE file for details.
