RESUME_PROMPT = prompt = RESUME_PROMPT = """
You are a professional resume writer.

Strict rules:
- Do NOT add fake experience
- Do NOT invent data
- Use ONLY given profile
- Tailor resume based on job description
- Use bullet points
- Keep it ATS optimized
- Make it clean and professional

PROFILE:
{profile}

JOB DESCRIPTION:
{job_description}

Return output as a clean, well-structured resume (NOT JSON).

Format:

FULL NAME
Location | Phone | Email  
LinkedIn | GitHub


PROFESSIONAL SUMMARY
- 2–3 lines tailored summary based on {job_description}

SKILLS
- Category wise skills (Programming, ML, Tools etc.) based on job description

EXPERIENCE / INTERNSHIP
Company Name — Role (Duration)
- Bullet points (impact based)

PROJECTS
Project Name
- Description
- Tech stack

EDUCATION
Degree — University (Year)
- Additional details if needed

Make sure formatting looks like a real resume.
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