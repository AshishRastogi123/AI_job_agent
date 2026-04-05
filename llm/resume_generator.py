from llm.llm_client import get_llm
from llm.prompts import RESUME_PROMPT

llm = get_llm()

def generate_resume(profile, job_description):
    prompt = RESUME_PROMPT.format(
        profile=profile,
        job_description=job_description
    )

    response = llm.invoke(prompt)
    return response.content
