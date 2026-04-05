from llm.llm_client import get_llm
from llm.prompts import COVER_LETTER_PROMPT

llm = get_llm()

def generate_cover_letter(profile, job_description):
    prompt = COVER_LETTER_PROMPT.format(
        profile=profile,
        job_description=job_description
    )
    response = llm.invoke(prompt)
    return response.content