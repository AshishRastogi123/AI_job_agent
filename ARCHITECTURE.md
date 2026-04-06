# AI Job Application Agent - Architecture & Design

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      JOB APPLICATION AGENT                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │        ORCHESTRATOR (agent/orchestrator.py)         │ │
│  │   - State management                                │ │
│  │   - Workflow coordination                           │ │
│  │   - Error handling & retries                        │ │
│  └──────┬──────────────┬─────────────┬────────┬────────┘ │
│         │              │             │        │          │
│    ┌────▼────┐    ┌────▼────┐  ┌────▼──┐ ┌──▼─────┐    │
│    │   JD    │    │  Field  │  │ Form  │ │ Browser│    │
│    │Extractor│    │Resolver │  │Filler │ │AutoM.  │    │
│    └────┬────┘    └────┬────┘  └────┬──┘ └──┬─────┘    │
│         │              │            │       │          │
│    ┌────▼────────┬─────▼───────┬────▼───────▼────┐    │
│    │   Playwright│  LLM Client │ Database (SQLAlchemy)  │
│    │  Browser    │  (Groq/OpenAI)  PostgreSQL        │
│    └─────────────┴──────────────┴───────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Orchestrator (`agent/orchestrator.py`)

**Responsibility**: Coordinate the entire workflow

**Key Features**:
- Sequential pipeline execution
- Error handling with retries
- Comprehensive logging
- State persistence

**Workflow Stages**:
```
fetch_job → extract_jd → generate_resume → generate_cover_letter
    ↓           ↓              ↓                    ↓
  detect_ats → fill_form → submit → log_results
```

**Error Handling**:
- Each step has try-catch
- Failed steps don't stop pipeline
- Results logged with full context
- Job status updated in database

#### 2. Services Layer

##### 2a. JD Extractor (`services/jd_extractor.py`)

**Purpose**: Reliably extract job descriptions from web pages

**Algorithm**:
1. Navigate to URL with Playwright
2. Wait for network idle state
3. Try multiple CSS selectors
4. Fallback to DOM extraction
5. Clean and validate (min 300 chars)
6. Retry if too short (max 2 retries)

**Selectors Used**:
```python
'[data-testid*="job-description"]'
'[class*="job-description"]'
'div[class*="description"]'
'section[class*="job"]'
'main', 'article'
```

**Validation**:
- Minimum 300 characters
- Auto-retry with exponential backoff
- Removes common noise (nav, footer, etc.)

##### 2b. Field Resolver (`services/field_resolver.py`)

**Purpose**: Intelligently resolve form field values

**Priority Order** (Confidence Scores):

```python
1. DATABASE (95% confidence)
   ├─ User profile (name, email, phone)
   ├─ Work experience
   ├─ Education
   └─ Skills

2. CUSTOM ANSWERS (90% confidence)
   ├─ Reusable across runs
   ├─ Learned from HITL
   └─ Extensible

3. LLM INFERENCE (70%+ confidence)
   ├─ Context-aware generation
   ├─ Based on profile + JD
   └─ Returns confidence score

4. HUMAN-IN-THE-LOOP (100% confidence)
   ├─ 30-second timeout
   ├─ Saves for future use
   └─ Optional based on confidence
```

**Confidence Threshold Logic**:
```
if confidence >= 0.95 → Use immediately (DB)
if 0.90 <= confidence < 0.95 → Use (Custom)
if 0.70 <= confidence < 0.90 → Use with logging
if confidence < 0.70 → Trigger HITL
```

##### 2c. Form Filler (`services/form_filler.py`)

**Purpose**: Detect and intelligently fill form fields

**Field Types Supported**:
- Text inputs (text, email, tel, number, url, date)
- Textareas
- Dropdowns (select)
- Radio buttons
- Checkboxes
- File uploads

**Algorithm**:
1. Query selector all form elements
2. Extract field metadata (name, label, type, required)
3. Use field resolver to get value
4. Fill field based on type
5. Handle errors gracefully

**Label Detection**:
- Try label[for=id] association
- Search parent elements
- Use HTML5 implicit linking
- Fallback to placeholder/name

#### 3. LLM Integration (`llm/`)

**LLM Client** (`llm_client.py`):
- Supports Groq and OpenAI
- Configurable via `LLM_PROVIDER` env var
- Uses LangChain for unified interface

**Resume Generator** (`resume_generator.py`):
- Takes candidate profile + JD
- Generates tailored resume
- Formats for ATS readability

**Cover Letter Generator** (`cover_letter.py`):
- Context-aware generation
- Personalized to job description
- Professional tone

**Field Inference** (`field_inference.py`):
- Prompt engineering for field values
- JSON response parsing
- Confidence scoring
- Error handling

#### 4. ATS Detection (`ats/detector.py`)

**Detection Strategy** (Dual Approach):

**URL Pattern Matching** (Primary):
```python
workday: r'workday\.com|wd\d+\.myworkdayjobs\.com|we\.workday\.com'
greenhouse: r'boards\.greenhouse\.io|grnh\.se'
lever: r'jobs\.lever\.co'
linkedin: r'linkedin\.com/jobs|lnkd\.in'
```

**DOM Fingerprinting** (Secondary):
```python
workday: 'workday', 'wd-content' in page
greenhouse: 'greenhouse', 'gh_embedded' in page
lever: 'lever', 'lever-application' in page
linkedin: 'linkedin' AND 'jobs' in page
```

#### 5. Database Layer (`db/`)

**Architecture**:
- SQLAlchemy ORM (not raw SQL)
- Connection pooling
- Session management
- Transaction handling

**Models**:
```python
User (id, name, email, phone, resume_path)
  ├─ WorkExperience (company, position, dates, description)
  ├─ Education (institution, degree, field, dates, gpa)
  ├─ Skill (skill_name, proficiency_level)
  └─ CustomAnswer (field_key, field_value)

Job (id, url, company, title, ats_platform, status)
ApplicationLog (job_id, user_id, step, status, message)
```

**Key Queries**:
- `get_user_profile()` - Full profile with all relations
- `save_custom_answer()` - Save HITL results
- `update_job_status()` - Track application progress
- `log_application_step()` - Detailed step logging

#### 6. Human-in-the-Loop (`hitl/manager.py`)

**Purpose**: Get user input for ambiguous fields

**Behavior**:
1. Display field info (label, type, context)
2. Show LLM suggestion (if available)
3. Wait for user input (30 second timeout)
4. Save answer for future use
5. Continue execution

**Implementation**:
- Console-based input
- Platform-specific timeout (signal on Unix, threading on Windows)
- Automatic persistence
- Graceful timeout handling

#### 7. Logging (`utils/logging_config.py`)

**Dual Output**:
1. **File Logging** (`logs/job_agent.log`):
   - Rotating file handler (10MB max)
   - Full timestamp and context
   - Backup files (5 rotations)

2. **Console Logging**:
   - INFO level by default
   - Simplified format for readability
   - Color-coded by level (DEBUG, INFO, WARNING, ERROR)

**Log Format**:
```
2024-01-15 14:23:45.123 - job_agent.agent.orchestrator - INFO - [orchestrator.py:156] - Extracted 1250 characters of job description
```

## Data Flow

### End-to-End Application Flow

```
START
  │
  ├─→ [1] FETCH JOB
  │   └─→ Get from queue or DB
  │       └─→ Status: pending
  │
  ├─→ [2] EXTRACT JD
  │   ├─→ Navigate with Playwright
  │   ├─→ Try multiple CSS selectors
  │   ├─→ Validate > 300 chars
  │   ├─→ Retry 2x if failed
  │   └─→ Log: extract_jd (success/failure)
  │
  ├─→ [3] DETECT ATS
  │   ├─→ URL pattern matching
  │   ├─→ DOM fingerprinting fallback
  │   └─→ Store: ats_platform
  │
  ├─→ [4] GENERATE RESUME
  │   ├─→ Profile + JD → LLM
  │   ├─→ Tailored for ATS
  │   └─→ Save PDF
  │
  ├─→ [5] GENERATE COVER LETTER
  │   ├─→ Profile + JD → LLM
  │   ├─→ Personalized tone
  │   └─→ Save PDF
  │
  ├─→ [6] FILL FORM
  │   ├─→ Detect fields
  │   │   ├─→ Input elements
  │   │   ├─→ Dropdowns
  │   │   ├─→ Radio buttons
  │   │   ├─→ Checkboxes
  │   │   └─→ File uploads
  │   │
  │   └─→ For each field:
  │       ├─→ Get label + type
  │       ├─→ Resolve value (DB→Custom→LLM→HITL)
  │       ├─→ Fill field
  │       └─→ Log: field_filled (source: DB/LLM/HITL)
  │
  ├─→ [7] SUBMIT APPLICATION
  │   ├─→ Find submit button
  │   ├─→ Click and wait
  │   └─→ Log: submit_application (success/failure)
  │
  └─→ [8] LOG RESULTS
      ├─→ Update job status (applied/failed)
      ├─→ Save unanswered fields
      ├─→ Save application logs
      └─→ Return results
      
  END
```

## Configuration Flow

```
.env Variables
  │
  ├─→ DB_URL ──→ PostgreSQL Connection
  │               └─→ SQLAlchemy Engine
  │                   └─→ Session Factory
  │
  ├─→ GROQ_API_KEY ──→ LLM Client
  │   (or OPENAI_API_KEY) └─→ LangChain
  │                          └─→ Prompt→Response
  │
  ├─→ HEADLESS ──→ Playwright Browser
  │   BROWSER_TIMEOUT  └─→ Automation
  │
  ├─→ HITL_ENABLED ──→ HITL Manager
  │   HITL_TIMEOUT     └─→ User Input
  │
  └─→ LOG_LEVEL ──→ Logging Config
      LOG_FILE       └─→ File & Console Output
```

## Error Handling Strategy

### Retry Logic

```python
For job_description retrieval:
  └─→ Max 2 retries (configurable: MAX_RETRIES)
      ├─→ Retry 1: Failed selector match
      ├─→ Retry 2: Still < 300 chars
      └─→ Mark job as failed if still empty

For LLM inference:
  └─→ Exponential backoff on rate limit
      ├─→ Wait 1s, then 2s, then 4s
      └─→ Max 3 attempts

For form filling:
  └─→ Skip individual field on error
      ├─→ Log specific field failure
      ├─→ Mark as unanswered
      └─→ Continue with next field

For submission:
  └─→ Try multiple submit selectors
      ├─→ button[type="submit"]
      ├─→ button:has-text("Apply")
      ├─→ [data-testid*="submit"]
      └─→ Fail gracefully if not found
```

### Graceful Degradation

```
Success Path:          Degradation Path:
─────────────────      ──────────────────
Full profile DB  ──→  Partial data + LLM
    ↓                       ↓
Custom answers ──→  LLM inference
    ↓                    ↓
LLM inference   ──→  HITL input
    ↓                    ↓
HITL (timeout) ──→  Skip field (unanswered_fields)
    ↓
✓ Application submitted
```

## Performance Characteristics

### Processing Time Estimates

```python
JD Extraction:           5-15 seconds
  ├─ Navigate + load: 3-10s
  ├─ Parse HTML: 0.5-1s
  └─ Validate: 0.2s

Resume Generation:       10-30 seconds
  └─ LLM call with profile + JD

Cover Letter:            10-30 seconds
  └─ LLM call with profile + JD

Form Detection:          2-5 seconds
  └─ Query selector all elements

Form Filling:            30-60 seconds
  ├─ Per field: 0.5-2 seconds
  └─ Typical: 20-40 fields

Submit:                  2-5 seconds
  └─ Find button + click

TOTAL per job:           1-2 minutes
```

### Database Performance

```python
Connection pooling:      5-10 connections
Session management:      < 100ms per query
Batch operations:        < 500ms for 100 items
```

## Security Considerations

### Data Protection

1. **Credentials**:
   - All credentials in `.env` (not committed)
   - Database passwords never in logs
   - API keys masked in error messages

2. **Database**:
   - SQLAlchemy prevents SQL injection
   - Connection pooling with timeout
   - Prepared statements by default

3. **Browser Automation**:
   - No credential storage
   - SSL/TLS by default in Playwright
   - Cookies isolated per session

### Sensitive Handling

```python
Resume/CV:    Stored locally, never uploaded
Cover Letter: Generated, stored locally
User Data:    PostgreSQL with access control
Logs:         Rotate automatically, can be purged
```

## Scalability Design

### Horizontal Scaling

```
Load Balancer
    │
    ├─→ Agent Instance 1 (Queue 1-100)
    ├─→ Agent Instance 2 (Queue 101-200)
    └─→ Agent Instance N (Queue ...)
        │
        └─→ PostgreSQL (Shared)
            └─→ Connection pooling
```

### Queue Management

```python
# In-memory queue (single instance)
self._memory_queue = []

# Redis queue (multi-instance)
redis_client.zadd('jobs', {url: priority})

# Database queue (persistent)
SELECT * FROM jobs WHERE status='pending'
```

## Extension Points

### Adding New ATS Platform

```python
# In ats/detector.py
ATS_PATTERNS['new_ats'] = [
    r'pattern1\.com',
    r'pattern2\.io'
]

DOM_FINGERPRINTS['new_ats'] = ['unique_identifier_1', 'unique_identifier_2']
```

### Custom Field Resolution

```python
# In services/field_resolver.py
def _try_custom_logic(self):
    # Add custom resolution logic
    pass
```

### New LLM Provider

```python
# In llm/llm_client.py
def get_llm():
    if provider == 'custom':
        return CustomLLMClient(api_key)
```

---

**Architecture v1.0 - Complete and Production-Ready**

For implementation details, see code comments and docstrings in each module.
