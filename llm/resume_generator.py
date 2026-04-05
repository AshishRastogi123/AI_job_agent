from llm.llm_client import get_llm
from llm.prompts import RESUME_PROMPT

llm = get_llm()

def generate_resume(profile,job_dicription):
    prompt=RESUME_PROMPT.format(
        profile=profile,
        job_dicription=job_dicription
    )

    response=llm.predict(prompt)
    return response