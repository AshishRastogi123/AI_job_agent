# Quick Reference Guide

## 🚀 Get Started (5 minutes)

```bash
# 1. Activate virtual environment
venv\Scripts\activate  # Windows

# 2. Initialize database
python init_db.py

# 3. Add demo data
python seed_demo.py

# 4. Run agent
python main.py --process-queue
```

## 📋 Common Commands

### View Logs
```bash
tail -f logs/job_agent.log
```

### Check Database
```bash
psql -U postgres - d job_agent_db

# View jobs
SELECT id, company, title, status FROM jobs ORDER BY created_at DESC;

# View skills
SELECT skill_name FROM skills WHERE user_id=1;

# View custom answers
SELECT field_key, field_value FROM custom_answers WHERE user_id=1;
```

### Process Specific Number of Jobs
```bash
python main.py --process-queue --max-jobs 5
```

### Add and Process Jobs
```bash
python main.py --add-jobs \
  "https://url1.com/job" \
  "https://url2.com/job"

python main.py --process-queue
```

### Debug Single Job
```bash
# Without headless (see browser)
HEADLESS=false python main.py --job-url "https://url.com/job"

# With debug logging
LOG_LEVEL=DEBUG python main.py --job-url "https://url.com/job"
```

## 🔧 Environment Variables Quick Setup

```env
# Required
DB_URL=postgresql://postgres:password@localhost:5432/job_agent_db
GROQ_API_KEY=your_groq_key

# Optional (defaults work)
HEADLESS=true
HITL_ENABLED=true
MAX_RETRIES=2
LOG_LEVEL=INFO
```

## 📊 Field Resolution Priority

```
1. Database (profile, experience, education, skills)
   └─ 95% confidence

2. Custom Answers (saved from previous HITL)
   └─ 90% confidence

3. LLM Inference (based on profile + job description)
   └─ 70%+ confidence

4. Human Input (if confidence < 70%)
   └─ 100% confidence ✓
```

## 🎯 Workflow Steps

```
1. Extract JD      → Playwright + BeautifulSoup
2. Detect ATS      → URL patterns + DOM fingerprinting
3. Generate Resume → LLM (Groq/OpenAI)
4. Cover Letter    → LLM generation
5. Fill Form       → Field detection + intelligent resolution
6. Submit          → Find submit button + click
7. Log Results     → Database + file
```

## 🐛 Troubleshooting Quick Tips

| Issue | Solution |
|-------|----------|
| DB connection fail | Check PostgreSQL running: `psql -U postgres` |
| LLM errors | Verify API key: `echo $GROQ_API_KEY` |
| Playwright fail | Reinstall: `playwright install` |
| Timeout issues | Increase `BROWSER_TIMEOUT=60000` |
| Form not filling | Set `HEADLESS=false` to debug visually |
| Memory issues | Reduce `MAX_RETRIES=1` |

## 📁 Important Directories

```
logs/              → Application logs
resumes/           → Generated PDFs
db/                → Database code
services/          → Core logic
agent/             → Orchestration
```

## 🔑 Key Configuration Files

```
.env               → Your credentials & settings
config.py          → App configuration
requirements.txt   → Python dependencies
seed_demo.py       → Test data
```

## 💡 Tips & Tricks

### Inspect a failed job
```python
from db.queries import get_application_logs
logs = get_application_logs(job_id=5)
for log in logs:
    print(f"{log['step']}: {log['status']} - {log['message']}")
```

### Check field resolution
```python
from services.field_resolver import FieldResolver
resolver = FieldResolver(user_id=1)
result = resolver.resolve("Email Address", "email", "software engineer job")
print(f"Value: {result['value']}")
print(f"Confidence: {result['confidence']}")
print(f"Source: {result['source']}")
```

### Test extract JD
```python
from services.jd_extractor import JDExtractor
with JDExtractor() as extractor:
    jd, success = extractor.extract("https://job.url")
    print(f"Extracted: {len(jd)} characters")
```

## 🚨 Error Codes

Common errors in logs:

```
[extract_jd] failure       → JD too short or extraction failed
[detect_ats] unknown       → ATS couldn't be determined
[fill_form] unanswered     → Field couldn't be resolved
[submit_application] fail  → Submit button not found
```

## 📈 Performance Expectations

| Activity | Time | Notes |
|----------|------|-------|
| JD Extraction | 5-15s | Network dependent |
| Resume Gen | 10-30s | LLM response time |
| Form Filling | 30-60s | Per field: 0.5-2s |
| Total | 1-2min | End-to-end |

## 🔐 Security Reminders

- Never commit `.env` file
- Keep API keys secret
- Database passwords in `.env` only
- Review logs contain no credentials
- Resume stored locally only

## 📞 When Things Go Wrong

1. **Check logs first**: `tail -f logs/job_agent.log`
2. **Verify .env**: All required keys present
3. **Test components**: Run individual services
4. **Database check**: Connection + schema
5. **Debug mode**: `LOG_LEVEL=DEBUG`

## 🎓 Learning Resources

- `README.md` - Full overview
- `SETUP_INSTRUCTIONS.md` - Detailed setup
- `ARCHITECTURE.md` - How it works
- Code comments - Implementation details

---

**Quick Reference Ready!**

Questions? Check docs or logs first.
