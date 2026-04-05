from llm.resume_generator import generate_resume

profile = {
    "name": "Ashish Rastogi",
    "skills": ["Python", "Machine Learning", "Deep Learning", "NLP"],
    "projects": [
        "Disease prediction system using ML",
        "AI job agent using LLMs"
    ],
    "experience": "Fresher / Intern",
    "education": "MCA"
}

job_description = """
Looking for AI Engineer with Python, ML, NLP experience.
Experience in building ML models and working with LLMs preferred.
"""

print(generate_resume(profile, job_description))