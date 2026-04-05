from typing import Dict, Optional, List
from db.profile_loader import load_profile
from llm.field_inference import infer_field
from hitl.manager import HITLManager

class FieldMapper:
    """Maps form fields to candidate data using priority logic"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.profile = load_profile(user_id)
        self.hitl_manager = HITLManager(user_id)

        # Field mapping patterns
        self.field_mappings = {
            'name': ['name', 'full_name', 'fullname', 'first_name', 'last_name'],
            'email': ['email', 'e-mail', 'email_address'],
            'phone': ['phone', 'telephone', 'mobile', 'cell'],
            'resume': ['resume', 'cv', 'curriculum_vitae'],
            'cover_letter': ['cover_letter', 'coverletter', 'personal_statement'],
            'linkedin': ['linkedin', 'linkedin_url', 'linkedin_profile'],
            'github': ['github', 'github_url', 'github_profile'],
            'portfolio': ['portfolio', 'portfolio_url', 'website'],
            'location': ['location', 'city', 'state', 'country', 'address'],
            'salary': ['salary', 'expected_salary', 'current_salary', 'compensation'],
            'experience': ['experience', 'years_experience', 'work_experience'],
            'education': ['education', 'degree', 'university', 'school']
        }

    def map_field(self, field_info: Dict, resume_path: Optional[str] = None, cover_letter_path: Optional[str] = None) -> Optional[str]:
        """
        Map a form field to candidate data using priority:
        1. Profile DB
        2. Custom answers
        3. LLM inference
        4. HITL fallback
        """
        field_name = field_info.get('name', '')
        field_label = field_info.get('label', '')
        field_placeholder = field_info.get('placeholder', '')

        # Combine field identifiers for matching
        field_text = f"{field_name} {field_label} {field_placeholder}".lower()

        # Priority 1: Direct profile match
        value = self._get_from_profile(field_text, resume_path, cover_letter_path)
        if value:
            return value

        # Priority 2: Custom answers
        value = self._get_from_custom_answers(field_text)
        if value:
            return value

        # Priority 3: LLM inference
        value = self._infer_field_value(field_text)
        if value:
            return value

        # Priority 4: HITL fallback
        if self.hitl_manager.should_fallback_to_hitl(field_text):
            return self.hitl_manager.request_human_input(field_text, field_info)

        return None

    def _get_from_profile(self, field_text: str, resume_path: Optional[str] = None, cover_letter_path: Optional[str] = None) -> Optional[str]:
        """Extract value from profile data"""
        # Name
        if any(keyword in field_text for keyword in self.field_mappings['name']):
            return self.profile.get('name')

        # Email
        if any(keyword in field_text for keyword in self.field_mappings['email']):
            return self.profile.get('email')

        # Phone
        if any(keyword in field_text for keyword in self.field_mappings['phone']):
            return self.profile.get('phone')

        # Resume path (for file uploads)
        if any(keyword in field_text for keyword in self.field_mappings['resume']):
            return resume_path or self.profile.get('resume_path')

        # Cover letter path (if it's a file upload)
        if any(keyword in field_text for keyword in self.field_mappings['cover_letter']):
            return cover_letter_path

        # Location (simplified - take first work location)
        if any(keyword in field_text for keyword in self.field_mappings['location']):
            if self.profile.get('work_experience'):
                # Could be enhanced to get current location
                return "New York, NY"  # Placeholder

        # Experience (years)
        if any(keyword in field_text for keyword in self.field_mappings['experience']):
            if self.profile.get('work_experience'):
                # Calculate total years
                total_years = len(self.profile['work_experience'])
                return str(total_years)

        return None

    def _get_from_custom_answers(self, field_text: str) -> Optional[str]:
        """Get value from custom answers DB"""
        custom_answers = self.profile.get('custom_answers', {})

        # Direct key match
        for key, value in custom_answers.items():
            if key.lower() in field_text:
                return value

        return None

    def _infer_field_value(self, field_text: str) -> Optional[str]:
        """Use LLM to infer field value"""
        try:
            return infer_field(field_text, self.profile)
        except Exception as e:
            print(f"LLM inference failed: {e}")
            return None

    def get_unanswered_fields(self, fields: List[Dict]) -> List[str]:
        """Get list of fields that couldn't be filled"""
        unanswered = []
        for field in fields:
            field_text = f"{field.get('name', '')} {field.get('label', '')} {field.get('placeholder', '')}"
            if not self.map_field(field):
                unanswered.append(field_text.strip())
        return unanswered