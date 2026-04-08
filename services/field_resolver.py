"""
Intelligent Field Resolver Service
Resolves form field values using priority order:
1. User profile database
2. Custom answers table
3. LLM inference
4. Human-in-the-loop
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.queries import get_user_profile, get_custom_answer, get_all_custom_answers, save_custom_answer
from llm.field_inference import infer_field_value
from hitl.manager import HITLManager
from config import HITL_ENABLED
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class FieldResolver:
    """Intelligently resolve form fields with confidence scoring"""
    
    # Common field patterns
    FIELD_PATTERNS = {
        'email': ['email', 'e-mail', 'contact email', 'email address'],
        'phone': ['phone', 'telephone', 'mobile', 'contact number', 'cell'],
        'name': ['full name', 'name', 'candidate name', 'your name'],
        'first_name': ['first name', 'given name'],
        'last_name': ['last name', 'surname', 'family name'],
        'location': ['location', 'city', 'residence', 'address', 'province', 'state', 'zip', 'postal', 'country'],
        'linkedin': ['linkedin', 'linkedin profile', 'linkedin url'],
        'github': ['github', 'github profile', 'github url'],
        'website': ['website', 'portfolio', 'personal website'],
        'resume': ['resume', 'cv', 'curriculum vitae', 'attachment', 'attach', 'upload'],
        'cover_letter': ['cover letter', 'coverletter', 'personal statement', 'motivation'],
        'education': ['degree', 'field of study', 'major', 'discipline', 'education'],
        'sensitive': ['gender', 'hispanic', 'latino', 'veteran', 'disability', 'race', 'ethnicity', 'citizenship', 'employment status', 'age']
    }
    
    CONFIDENCE_THRESHOLDS = {
        'db': 0.95,           # DB answers are highly confident
        'custom': 0.90,       # Custom answers are also high confidence
        'llm': 0.70,          # LLM needs confidence > 0.7
    }
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.hitl_manager = HITLManager(user_id) if HITL_ENABLED else None
        self.user_profile = get_user_profile(user_id)
    
    def resolve(self, field_label: str, field_type: str, context: str = "") -> Dict:
        """
        Resolve a field value with confidence score
        
        Returns:
            {
                'value': str,
                'confidence': float (0-1),
                'source': str (DB/CUSTOM/LLM/HITL/SKIPPED),
                'reasoning': str
            }
        """
        logger.info(f"Resolving field: {field_label} (type: {field_type})")
        
        # 1. Try database first
        result = self._try_database(field_label, field_type)
        if result and result.get('confidence', 0) >= self.CONFIDENCE_THRESHOLDS['db']:
            logger.info(f"  → Found in DB with confidence {result['confidence']}")
            return result
        
        # 2. Try custom answers
        result = self._try_custom_answers(field_label)
        if result and result.get('confidence', 0) >= self.CONFIDENCE_THRESHOLDS['custom']:
            logger.info(f"  → Found in custom answers")
            return result
        
        # 3. Try LLM inference
        result = self._try_llm_inference(field_label, field_type, context)
        threshold = self._get_llm_threshold(field_label, field_type)
        if result and result.get('confidence', 0) >= threshold:
            logger.info(f"  → LLM inferred with confidence {result['confidence']}")
            return result

        # 4. Try HITL for non-sensitive fields only
        if HITL_ENABLED and result and result.get('confidence', 0) < threshold and not self._is_sensitive_field(field_label):
            logger.info(f"  → Confidence too low ({result['confidence']}), triggering HITL")
            hitl_value = self.hitl_manager.request_human_input(field_label, {
                'type': field_type,
                'llm_suggestion': result.get('value'),
                'context': context
            })
            if hitl_value:
                save_custom_answer(self.user_id, field_label, hitl_value)
                return {
                    'value': hitl_value,
                    'confidence': 1.0,
                    'source': 'HITL',
                    'reasoning': 'Provided by user'
                }
        
        # Field couldn't be resolved
        return {
            'value': '',
            'confidence': 0,
            'source': 'SKIPPED',
            'reasoning': 'Could not resolve with confidence'
        }
    
    def _try_database(self, field_label: str, field_type: str) -> Dict:
        """Try to find value in user database"""
        try:
            normalized_label = field_label.lower()

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['email']) and self.user_profile.get('email'):
                return {
                    'value': self.user_profile['email'],
                    'confidence': 0.95,
                    'source': 'DB',
                    'reasoning': 'From user profile email'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['phone']) and self.user_profile.get('phone'):
                return {
                    'value': self.user_profile['phone'],
                    'confidence': 0.95,
                    'source': 'DB',
                    'reasoning': 'From user profile phone'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['first_name']) and self.user_profile.get('name'):
                return {
                    'value': self.user_profile['name'].split()[0],
                    'confidence': 0.90,
                    'source': 'DB',
                    'reasoning': 'Extracted first name from profile'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['last_name']) and self.user_profile.get('name'):
                parts = self.user_profile['name'].split()
                return {
                    'value': ' '.join(parts[1:]) if len(parts) > 1 else parts[0],
                    'confidence': 0.90,
                    'source': 'DB',
                    'reasoning': 'Extracted last name from profile'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['name']) and self.user_profile.get('name'):
                return {
                    'value': self.user_profile['name'],
                    'confidence': 0.95,
                    'source': 'DB',
                    'reasoning': 'From user profile name'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['resume']):
                resume_path = self.user_profile.get('resume_path')
                if resume_path:
                    return {
                        'value': resume_path,
                        'confidence': 0.95,
                        'source': 'DB',
                        'reasoning': 'From user resume path'
                    }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['education']) and self.user_profile.get('education'):
                education = self.user_profile['education'][0]
                if 'degree' in normalized_label:
                    return {
                        'value': education.get('degree', ''),
                        'confidence': 0.90,
                        'source': 'DB',
                        'reasoning': 'From user education degree'
                    }
                if any(key in normalized_label for key in ['field of study', 'discipline', 'major']):
                    return {
                        'value': education.get('field_of_study', ''),
                        'confidence': 0.90,
                        'source': 'DB',
                        'reasoning': 'From user education field of study'
                    }
                if 'institution' in normalized_label:
                    return {
                        'value': education.get('institution', ''),
                        'confidence': 0.85,
                        'source': 'DB',
                        'reasoning': 'From user education institution'
                    }
                if 'end date' in normalized_label or 'end year' in normalized_label:
                    return {
                        'value': education.get('end_date', ''),
                        'confidence': 0.80,
                        'source': 'DB',
                        'reasoning': 'From user education end date'
                    }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['location']):
                location = self.user_profile.get('location')
                if location:
                    return {
                        'value': location,
                        'confidence': 0.85,
                        'source': 'DB',
                        'reasoning': 'From user profile location'
                    }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['linkedin']) and self.user_profile.get('linkedin'):
                return {
                    'value': self.user_profile['linkedin'],
                    'confidence': 0.90,
                    'source': 'DB',
                    'reasoning': 'From user profile linkedin'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['github']) and self.user_profile.get('github'):
                return {
                    'value': self.user_profile['github'],
                    'confidence': 0.90,
                    'source': 'DB',
                    'reasoning': 'From user profile github'
                }

            if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['website']) and self.user_profile.get('website'):
                return {
                    'value': self.user_profile['website'],
                    'confidence': 0.85,
                    'source': 'DB',
                    'reasoning': 'From user profile website'
                }

            if 'skill' in normalized_label and self.user_profile.get('skills'):
                skills_str = ', '.join([s.get('skill_name', s.get('name', '')) for s in self.user_profile['skills']])
                return {
                    'value': skills_str,
                    'confidence': 0.85,
                    'source': 'DB',
                    'reasoning': 'From user skills'
                }

            if ('experience' in normalized_label or 'company' in normalized_label) and self.user_profile.get('work_experience'):
                exp = self.user_profile['work_experience'][0] if self.user_profile['work_experience'] else None
                if exp:
                    if 'company' in normalized_label:
                        return {
                            'value': exp.get('company', ''),
                            'confidence': 0.85,
                            'source': 'DB',
                            'reasoning': 'From latest work experience'
                        }
                    if 'position' in normalized_label or 'title' in normalized_label:
                        return {
                            'value': exp.get('position', ''),
                            'confidence': 0.85,
                            'source': 'DB',
                            'reasoning': 'From latest work position'
                        }
                    if 'end date' in normalized_label or 'end year' in normalized_label:
                        return {
                            'value': exp.get('end_date', ''),
                            'confidence': 0.80,
                            'source': 'DB',
                            'reasoning': 'From latest work experience end date'
                        }
        except Exception as e:
            logger.warning(f"Error accessing database: {e}")

        return None
    
    def _try_custom_answers(self, field_label: str) -> Dict:
        """Try to find value in custom answers"""
        try:
            custom_answers = get_all_custom_answers(self.user_id)
            
            # Exact match
            if field_label in custom_answers:
                return {
                    'value': custom_answers[field_label],
                    'confidence': 0.90,
                    'source': 'CUSTOM',
                    'reasoning': 'From custom answers'
                }
            
            # Fuzzy match
            normalized_label = field_label.lower()
            for key, value in custom_answers.items():
                if normalized_label in key.lower() or key.lower() in normalized_label:
                    return {
                        'value': value,
                        'confidence': 0.75,
                        'source': 'CUSTOM',
                        'reasoning': f'Fuzzy match with {key}'
                    }
        
        except Exception as e:
            logger.warning(f"Error accessing custom answers: {e}")
        
        return None
    
    def _try_llm_inference(self, field_label: str, field_type: str, context: str) -> Dict:
        """Try to infer value using LLM"""
        try:
            result = infer_field_value(
                field_label=field_label,
                field_type=field_type,
                user_profile=self.user_profile,
                job_context=context
            )
            
            if result and result.get('value'):
                return {
                    'value': result['value'],
                    'confidence': result.get('confidence', 0.65),
                    'source': 'LLM',
                    'reasoning': result.get('reasoning', 'LLM inference')
                }
        
        except Exception as e:
            logger.warning(f"Error during LLM inference: {e}")
        
        return None

    def _get_llm_threshold(self, field_label: str, field_type: str) -> float:
        normalized_label = field_label.lower()
        if field_type == 'textarea':
            return 0.50
        if any(keyword in normalized_label for keyword in ['why', 'describe', 'explain', 'subject areas', 'expertise', 'experience']):
            return 0.55
        if any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['education']):
            return 0.55
        return self.CONFIDENCE_THRESHOLDS['llm']

    def _is_sensitive_field(self, field_label: str) -> bool:
        normalized_label = field_label.lower()
        return any(keyword in normalized_label for keyword in self.FIELD_PATTERNS['sensitive'])
