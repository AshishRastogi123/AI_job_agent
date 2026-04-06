# AI Job Application Agent

A production-ready autonomous job application system that intelligently fills out job application forms, tailors resumes, and applies to jobs automatically using AI and browser automation.

## 🎯 Features

✅ **End-to-End Automation**
- Fetches jobs from queue
- Extracts job descriptions reliably
- Generates tailored resumes & cover letters
- Detects ATS platforms (Workday, Greenhouse, Lever)
- Intelligently fills ALL form fields
- Submits applications automatically
- Comprehensive error handling & retries

✅ **Intelligent Field Resolution**
- Priority-based resolution: DB → Custom Answers → LLM → HITL
- Confidence scoring for each field
- Human-in-the-loop for uncertain fields
- Extensible custom answers table

✅ **Production Features**
- SQLAlchemy + PostgreSQL database
- Comprehensive logging (file & console)
- Retry logic with exponential backoff
- Job tracking and status management
- Application logs for debugging
- Clean modular architecture

## 📋 Quick Start

### 1. Prerequisites

- **Python 3.8+**
- **PostgreSQL 12+**
- **Redis** (optional, for job queue)

### 2. Setup Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 3. Configure Database

Create `.env` file:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_agent_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_URL=postgresql://postgres:password@localhost:5432/job_agent_db

# LLM
GROQ_API_KEY=your_key_here
LLM_PROVIDER=groq

# Application
HEADLESS=true
HITL_ENABLED=true
MAX_RETRIES=2
LOG_LEVEL=INFO
```

Create PostgreSQL database:
```bash
createdb job_agent_db
```

### 4. Initialize Database

```bash
python init_db.py
python seed_demo.py
```

### 5. Run Agent

```bash
# Single job application
python main.py --job-url "https://example.com/job"

# Process queue
python main.py --process-queue

# Add jobs to queue
python main.py --add-jobs "https://url1.com/job" "https://url2.com/job"

# Specify user
python main.py --user-id 1 --process-queue
```

## 🏗️ Architecture

### Directory Structure

```
ai_job_agent/
├── agent/                    # Orchestration
│   └── orchestrator.py      # Main workflow engine
├── services/                # Core business logic
│   ├── jd_extractor.py      # Job description extraction
│   ├── field_resolver.py    # Intelligent field resolution
│   └── form_filler.py       # Form filling engine
├── db/                      # Database layer
│   ├── connection.py        # SQLAlchemy setup
│   ├── models.py            # SQLAlchemy ORM models
│   └── queries.py           # Database operations
├── browser/                 # Browser automation
│   └── automation.py        # Playwright wrapper
├── ats/                     # ATS detection
│   └── detector.py          # Platform detection
├── llm/                     # LLM integration
│   ├── llm_client.py        # LLM client (Groq/OpenAI)
│   ├── resume_generator.py  # Resume generation
│   ├── cover_letter.py      # Cover letter generation
│   └── field_inference.py   # Field value inference
├── hitl/                    # Human-in-the-loop
│   └── manager.py           # HITL orchestration
├── job_queue/               # Job queue management
│   └── manager.py           # Queue operations
├── utils/                   # Utilities
│   ├── logging_config.py    # Logging setup
│   ├── pdf_utils.py         # PDF generation
│   └── field_mapper.py      # Field mapping
├── resumes/                 # Generated PDFs
├── logs/                    # Application logs
├── main.py                  # CLI entry point
├── config.py                # Configuration
├── init_db.py              # Database initialization
├── seed_demo.py            # Demo data
└── requirements.txt        # Dependencies
```

### Data Flow

```
┌─────────────┐
│  Job Queue  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ Fetch Job + Extract JD   │
│ (Playwright + BeautifulSoup)
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Detect ATS Platform      │
│ (URL + DOM fingerprinting)
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Generate Resume/Cover    │
│ (LLM - Groq/OpenAI)      │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Open Browser & Fill Form │
│ Intelligent Field Resolver
│  1. DB Query             │
│  2. Custom Answers       │
│  3. LLM Inference        │
│  4. Human-in-the-Loop    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Submit Application       │
│ + Log Results           │
└──────────────────────────┘
```

## 📊 Database Schema

### Users
Candidate profiles with education, work experience, and skills

### Custom Answers
Extensible key-value store for form fields (reusable across runs)

### Jobs
Job application tracking with ATS detection and status management

### Application Logs
Step-by-step execution logs for debugging

### Support Tables
- `work_experience`: Professional background
- `education`: Academic credentials
- `skills`: Technical capabilities

## 🧠 Field Resolution Logic

The system intelligently resolves form fields using:

1. **Database (95% confidence)**
   - User profile (name, email, phone)
   - Work experience
   - Education
   - Skills

2. **Custom Answers (90% confidence)**
   - Reusable across applications
   - Learned from previous HITL inputs
   - Extensible key-value store

3. **LLM Inference (70% confidence)**
   - Context-aware value generation
   - Based on full candidate profile + JD
   - Returns confidence score

4. **Human-in-the-Loop**
   - Triggered when confidence < 70%
   - 30-second timeout
   - Saves answer for future use

## 🎯 ATS Platform Support

| Platform | Detection Method | Pattern Examples |
|----------|------------------|------------------|
| **Workday** | URL + DOM | `myworkdayjobs.com`, `wd5.myworkdayjobs.com` |
| **Greenhouse** | URL + DOM | `boards.greenhouse.io`, `grnh.se` |
| **Lever** | URL + DOM | `jobs.lever.co` |
| **LinkedIn** | URL + DOM | `linkedin.com/jobs` |

## 🔧 Form Filling Engine

Supports all input types:
- Text inputs (name, email, phone, etc.)
- Email fields
- Dropdowns
- Radio buttons
- Checkboxes
- File uploads (resume attachment)
- Textareas

## 📝 Logging

All activities logged to `logs/job_agent.log`:
- Job start/end with timestamps
- JD extraction success/failure
- ATS platform detection
- Field resolution source (DB/LLM/HITL)
- Errors with full context
- Application results

## ⚙️ Configuration

### Environment Variables

```env
# Database
DB_URL=postgresql://user:pass@localhost:5432/job_agent_db

# LLM
GROQ_API_KEY=your_groq_api_key
LLM_PROVIDER=groq  # or 'openai'

# Browser
HEADLESS=true
BROWSER_TIMEOUT=30000  # milliseconds

# HITL
HITL_ENABLED=true
HITL_TIMEOUT=30  # seconds

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/job_agent.log

# Application
MAX_RETRIES=2
DEBUG=false
```

## 🚀 Example Usage

### Process Single Job
```bash
python main.py --job-url "https://jobs.example.com/senior-engineer"
```

### Process All Pending Jobs
```bash
python main.py --user-id 1 --process-queue --max-jobs 10
```

### Add Multiple Jobs to Queue
```bash
python main.py --add-jobs \
  "https://greenhouse.io/job1" \
  "https://workday.io/job2" \
  "https://lever.co/job3"
```

## 🔍 Monitoring

Check application status:
```bash
# View recent logs
tail -f logs/job_agent.log

# Check job status in database
psql job_agent_db
SELECT * FROM jobs ORDER BY created_at DESC;
```

## 📈 Performance

- **JD Extraction**: 5-15 seconds per job
- **Resume/Cover Letter Generation**: 10-30 seconds
- **Form Filling**: 30-60 seconds depending on form complexity
- **Average Application**: 1-2 minutes end-to-end

## 🛠️ Production Deployment

### Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

COPY . .

CMD ["python", "main.py", "--process-queue"]
```

### Database Backups
```bash
pg_dump job_agent_db > backup.sql
psql job_agent_db < backup.sql
```

## 🐛 Troubleshooting

### Database Connection Failed
- Check PostgreSQL is running: `psql postgres`
- Verify credentials in `.env`
- Check database exists: `psql -l | grep job_agent`

### LLM Errors
- Check API key is valid
- Check rate limits (Groq/OpenAI)
- Verify network connectivity

### Form Filling Issues
- Enable verbose logging: `LOG_LEVEL=DEBUG`
- Check browser headless mode disabled: `HEADLESS=false`
- Inspect HTML structure of form

### Timeout Issues
- Increase `BROWSER_TIMEOUT` value
- Check network speed
- Try disabling headless mode for debugging

## 📚 Key Modules

### JDExtractor
```python
from services.jd_extractor import JDExtractor

with JDExtractor() as extractor:
    jd, success = extractor.extract("https://job.url")
```

### FieldResolver  
```python
from services.field_resolver import FieldResolver

resolver = FieldResolver(user_id=1)
result = resolver.resolve("Email Address", "email", context)
# Returns: {value, confidence, source, reasoning}
```

### FormFillingEngine
```python
from services.form_filler import FormFillingEngine

filler = FormFillingEngine(page, user_id=1)
result = filler.fill_forms(job_description)
# Returns: {filled_count, unanswered, errors}
```

## 🔐 Security

- No credentials hardcoded (environment variables only)
- Database connections use connection pooling
- SQL injection prevention via SQLAlchemy ORM
- Sensitive logs masked in output
- Resume files stored locally (not uploaded)

## 📄 License

This project is provided as-is for educational and professional use.

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- Support for more ATS platforms
- Improved resume tailoring
- Advanced field inference
- Multi-language support
- Retry with exponential backoff
- Webhook notifications

## ✨ Next Steps

1. Configure your PostgreSQL database
2. Set up your LLM API keys
3. Run `python init_db.py` to create schema
4. Run `python seed_demo.py` to add test data
5. Run `python main.py --process-queue` to start applications

---

**Built with ❤️ for autonomous job applications**


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
