RESUME_PROMPT = prompt = """
You are a professional resume writer.

Strict rules:
- Do NOT add fake experience
- Do NOT invent data
- Use ONLY given profile
- Tailor resume based on job description
- Use bullet points
- Keep it ATS optimized

PROFILE:
{profile}

JOB DESCRIPTION:
{job_description}

Return output in JSON format:
{{
  "name": "",
  "title": "",
  "summary": "",
  "skills": [],
  "experience": [],
  "projects": [],
  "education": []
}}
"""

COVER_LETTER_PROMPT = """
Write a professional cover letter.

Candidate:
{profile}

Job:
{job_description}
"""

FIELD_INFERENCE_PROMPT = """
You are filling a job application form.

Candidate Profile:
{profile}

Field:
{field_name}

Give a concise answer suitable for job applications.
"""