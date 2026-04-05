from llm.llm_client import get_llm
from llm.prompts import COVER_LETTER_PROMPT

llm=get_llm()

def infer_field(profile, job_description):
    prompt=COVER_LETTER_PROMPT.format(
        profile=profile,
        job_description=job_description

    )
    return llm.predict(prompt)