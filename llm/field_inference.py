"""
LLM-based field inference for intelligent form filling
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.llm_client import get_llm
import json
import logging

logger = logging.getLogger(__name__)


def infer_field_value(field_label: str, field_type: str, user_profile: dict, job_context: str = "") -> dict:
    """
    Use LLM to infer field value based on profile and job context
    
    Returns:
        {
            'value': str,
            'confidence': float (0-1),
            'reasoning': str
        }
    """
    try:
        llm = get_llm()
        
        prompt = _build_inference_prompt(field_label, field_type, user_profile, job_context)
        
        response = llm.invoke(prompt)
        
        # Parse response to extract value and confidence
        result = _parse_inference_response(response.content)
        
        return result
    
    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        return {
            'value': '',
            'confidence': 0,
            'reasoning': f'Inference failed: {str(e)}'
        }


def _build_inference_prompt(field_label: str, field_type: str, profile: dict, job_context: str) -> str:
    """Build prompt for LLM field inference"""
    
    profile_str = _format_profile(profile)
    
    prompt = f"""
You are an AI assistant helping fill out job application forms intelligently.

CANDIDATE PROFILE:
{profile_str}

JOB CONTEXT:
{job_context if job_context else "No job description provided"}

FIELD TO FILL:
Label: {field_label}
Type: {field_type}

Based on the candidate profile and job context, infer the most appropriate value for this field.

Respond ONLY with a JSON object in this exact format:
{{
    "value": "the inferred value",
    "confidence": 0.85,
    "reasoning": "why this value was chosen"
}}

If you cannot infer a reasonable value, use empty string and low confidence (< 0.5).
"""
    
    return prompt


def _format_profile(profile: dict) -> str:
    """Format user profile for LLM context"""
    if not profile:
        return "No profile information available"
    
    lines = []
    
    if profile.get('name'):
        lines.append(f"Name: {profile['name']}")
    if profile.get('email'):
        lines.append(f"Email: {profile['email']}")
    if profile.get('phone'):
        lines.append(f"Phone: {profile['phone']}")
    
    if profile.get('work_experience'):
        lines.append("\nWork Experience:")
        for exp in profile['work_experience'][:3]:  # Last 3 positions
            lines.append(f"  - {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')}")
            if exp.get('description'):
                lines.append(f"    {exp['description'][:100]}...")
    
    if profile.get('education'):
        lines.append("\nEducation:")
        for edu in profile['education']:
            lines.append(f"  - {edu.get('degree', 'N/A')} in {edu.get('field_of_study', 'N/A')}")
            if edu.get('institution'):
                lines.append(f"    from {edu['institution']}")
    
    if profile.get('skills'):
        skills = [s.get('skill_name', '') for s in profile['skills']]
        lines.append(f"\nSkills: {', '.join(skills)}")
    
    if profile.get('custom_answers'):
        lines.append("\nAdditional Information:")
        for key, value in profile['custom_answers'].items():
            lines.append(f"  - {key}: {value}")
    
    return "\n".join(lines)


def _parse_inference_response(response_text: str) -> dict:
    """Parse LLM response to extract value and confidence"""
    try:
        # Try to extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            return {
                'value': str(result.get('value', '')).strip(),
                'confidence': float(result.get('confidence', 0)),
                'reasoning': str(result.get('reasoning', 'LLM inference'))
            }
    
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}")
    
    return {
        'value': '',
        'confidence': 0,
        'reasoning': 'Failed to parse LLM response'
    }
