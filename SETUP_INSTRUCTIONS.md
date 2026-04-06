# AI Job Application Agent - Complete Setup Guide

## System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for virtual environment + dependencies

## Step-by-Step Setup

### Phase 1: Environment Setup

#### 1.1 Create Virtual Environment

```bash
# Navigate to project directory
cd d:\Job_agent\AI_job_agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

#### 1.2 Install Dependencies

```bash
# Update pip
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Install Playwright browsers (required for automation)
playwright install

# Verify installation
python -c "import sqlalchemy, playwright, langchain; print('✓ All packages installed successfully')"
```

### Phase 2: Database Setup

#### 2.1 PostgreSQL Configuration

Ensure PostgreSQL is running:

```bash
# On Windows (if using PostgreSQL service):
net start postgresql-x64-15  # version may vary

# On Linux:
sudo service postgresql start

# On macOS with Homebrew:
brew services start postgresql
```

#### 2.2 Create Database

```bash
# Access PostgreSQL
psql -U postgres

# Create database (in psql shell):
CREATE DATABASE job_agent_db;

# Verify creation:
\l

# Exit psql:
\q
```

#### 2.3 Create .env Configuration File

Copy the example:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# ============ DATABASE CONFIGURATION ============
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_agent_db
DB_USER=postgres
DB_PASSWORD=your_postgresql_password  # Change this!
DB_URL=postgresql://postgres:your_postgresql_password@localhost:5432/job_agent_db

# ============ LLM CONFIGURATION ============
# Using Groq (fast, free tier available)
GROQ_API_KEY=your_groq_api_key_here
# Get from: https://console.groq.com/keys

# Alternative: OpenAI
# OPENAI_API_KEY=your_openai_api_key_here

LLM_PROVIDER=groq  # or 'openai'

# ============ BROWSER AUTOMATION ============
HEADLESS=true       # Set to false for debugging/testing
BROWSER_TIMEOUT=30000  # milliseconds

# ============ HUMAN-IN-THE-LOOP ============
HITL_ENABLED=true
HITL_TIMEOUT=30     # seconds to wait for user input

# ============ LOGGING ============
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/job_agent.log
DEBUG=false

# ============ APPLICATION SETTINGS ============
MAX_RETRIES=2
```

**Important**: 
- Replace `your_postgresql_password` with your actual PostgreSQL password
- Get GROQ_API_KEY from: https://console.groq.com/keys
- Keep these credentials secure!

### Phase 3: Database Initialization

```bash
# Create database schema
python init_db.py

# Expected output:
# ✅ Database initialized successfully!
# Next step: Run 'python seed_demo.py' to add demo data.
```

### Phase 4: Seed Demo Data

```bash
# Add demo candidate profile and job listings
python seed_demo.py

# Expected output:
# ============================================================
# 🚀 Demo data seeded successfully!
# ============================================================
# User ID: 1
# Name: Alex Johnson
# Email: demo@example.com
# Jobs added: 6
#
# You can now run the agent:
#   python main.py --user-id 1 --process-queue
# ============================================================
```

The demo data includes:
- **1 Candidate Profile** (Alex Johnson) with:
  - 3 years of work experience
  - 2 education records (MS + BS in Computer Science)
  - 15 technical skills
  - 9 custom answers (LinkedIn, GitHub, location, etc.)
- **6 Job Listings** across:
  - 2 Greenhouse job boards
  - 2 Workday job portals
  - 2 Lever job boards

### Phase 5: Verify Setup

```bash
# Check database connection
python -c "from db.connection import get_session; s = get_session(); s.close(); print('✓ Database connection working')"

# Check LLM connectivity
python -c "from llm.llm_client import get_llm; llm = get_llm(); print('✓ LLM provider configured')"

# Check package imports
python -c "from agent.orchestrator import JobApplicationAgent; print('✓ All imports working')"
```

## Running the Agent

### Option 1: Process Demo Jobs

```bash
python main.py --user-id 1 --process-queue
```

This will:
1. ✓ Fetch first pending job from database
2. ✓ Extract job description from the URL
3. ✓ Generate tailored resume
4. ✓ Generate cover letter
5. ✓ Detect ATS platform
6. ✓ Fill out application form
7. ✓ Submit application
8. ✓ Repeat for remaining jobs

### Option 2: Apply to Single Job

```bash
python main.py --job-url "https://boards.greenhouse.io/techcompany/jobs/4234512" --user-id 1
```

### Option 3: Add Jobs and Process

```bash
# Add new jobs to queue
python main.py --add-jobs \
  "https://jobs.lever.co/company/position-1" \
  "https://company.wd5.myworkdayjobs.com/job/title"

# Then process them
python main.py --process-queue
```

## Testing the Setup

### 1. Database Test

```bash
psql -U postgres -d job_agent_db

# View seeded user:
SELECT id, name, email, phone FROM users;

# View jobs:
SELECT url, company, title, ats_platform, status FROM jobs;

# View skills:
SELECT user_id, skill_name, proficiency_level FROM skills;

# Exit:
\q
```

### 2. End-to-End Test

```bash
# Run with a single job in non-headless mode for visual feedback
python main.py --job-url "YOUR_TEST_URL" --user-id 1

# Watch the browser open and forms being filled
# Set HEADLESS=false in .env to see the browser
```

### 3. Check Logs

```bash
# View live logs
tail -f logs/job_agent.log

# Or open with your editor
code logs/job_agent.log
```

## Troubleshooting

### PostgreSQL Connection Failed

**Error**: `psycopg2.OperationalError: connection failed`

**Solutions**:
1. Check PostgreSQL is running:
   ```bash
   # Windows:
   tasklist | findstr postgres
   
   # Linux:
   ps aux | grep postgres
   ```

2. Verify credentials in `.env`:
   ```bash
   psql -U postgres -h localhost
   ```

3. Test connection directly:
   ```python
   import psycopg2
   psycopg2.connect("dbname=job_agent_db user=postgres password=YOUR_PASSWORD host=localhost")
   ```

### LLM API Key Error

**Error**: `AuthenticationError: Invalid API key`

**Solution**:
1. Verify key in `.env`: `echo $GROQ_API_KEY`
2. Get new key from: https://console.groq.com/keys
3. Test connectivity:
   ```python
   from llm.llm_client import get_llm
   llm = get_llm()
   result = llm.invoke("Test message")
   ```

### Browser/Playwright Error

**Error**: `playwright._impl._errors.Error: Executable doesn't exist`

**Solution**:
```bash
# Reinstall browsers
playwright install

# Check installation
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop(); print('✓')"
```

### Memory Issues

If running out of memory:
1. Disable headless mode: `HEADLESS=true` (default)
2. Reduce `MAX_RETRIES` in `.env`
3. Close other applications
4. Increase virtual memory on system

### Timeout Issues

If forms take too long to fill:
1. Increase `BROWSER_TIMEOUT` in `.env` (in milliseconds)
2. Increase `HITL_TIMEOUT` for human input
3. Check network connectivity
4. Disable `HEADLESS=false` to debug visual issues

## Performance Tuning

### For Faster Processing

```env
# .env configuration
HEADLESS=true              # Disable UI rendering
BROWSER_TIMEOUT=15000      # Faster timeout
MAX_RETRIES=1              # Fewer retries
LOG_LEVEL=WARNING          # Less logging overhead
```

### For More Reliable Results

```env
HEADLESS=false             # Visual debugging
BROWSER_TIMEOUT=60000      # More time
MAX_RETRIES=3             # More attempts
LOG_LEVEL=DEBUG           # Full logging
HITL_ENABLED=true         # Manual intervention when needed
```

## Production Deployment

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py", "--process-queue"]
```

Build and run:
```bash
docker build -t job-agent .
docker run -e DB_URL=postgresql://... -e GROQ_API_KEY=... job-agent
```

### Database Backup

```bash
# Backup
pg_dump -U postgres job_agent_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U postgres job_agent_db < backup_20240101.sql
```

## Monitoring

### View Application Logs

```bash
# Recent logs
tail -50 logs/job_agent.log

# Follow live logs
tail -f logs/job_agent.log

# Search logs
grep "ERROR" logs/job_agent.log
grep "job_id=5" logs/job_agent.log
```

### Check Job Status

```bash
psql -U postgres -d job_agent_db -c "SELECT id, company, title, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;"
```

### View Application Logs from Database

```bash
psql -U postgres -d job_agent_db -c "SELECT job_id, step, status, message, created_at FROM application_logs ORDER BY created_at DESC LIMIT 50;"
```

## Next Steps

1. ✅ Environment configured
2. ✅ Database initialized
3. ✅ Demo data loaded
4. → Run first application: `python main.py --process-queue`
5. → Monitor logs: `tail -f logs/job_agent.log`
6. → Review results in database
7. → Add your own job URLs
8. → Deploy to production (optional)

## Support & Troubleshooting

For issues or questions:
1. Check logs: `logs/job_agent.log`
2. Review database status
3. Verify `.env` configuration
4. Test components individually

---

**Setup Complete!** 🎉

Your AI Job Application Agent is ready to autonomously fill out job applications.

Start with: `python main.py --process-queue`
