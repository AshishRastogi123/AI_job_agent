RESUME_PROMPT = """
You are an expert ATS resume optimizer.

Rewrite the candidate resume to match the job description.

Focus on:
- ATS keywords
- measurable impact
- relevant skills

Candidate Profile:
{profile}

Job Description:
{job_description}

Return only the improved resume.
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