from llm.llm_client import get_llm
from llm.prompts import FIELD_INFERENCE_PROMPT

llm = get_llm()

def infer_field(field_name, profile):
    prompt = FIELD_INFERENCE_PROMPT.format(
        field_name=field_name,
        profile=profile
    )
    response = llm.invoke(prompt)
    return response.content