import re
from typing import Optional

class ATSDetector:
    """Detect ATS platform from URL patterns and DOM fingerprinting"""

    ATS_PATTERNS = {
        'workday': [
            r'workday\.com',
            r'wd\d+\.myworkdayjobs\.com',
            r'we\.workday\.com'
        ],
        'greenhouse': [
            r'boards\.greenhouse\.io',
            r'grnh\.se'
        ],
        'lever': [
            r'jobs\.lever\.co'
        ],
        'linkedin': [
            r'linkedin\.com/jobs',
            r'lnkd\.in'
        ]
    }

    @staticmethod
    def detect_from_url(url: str) -> Optional[str]:
        """Detect ATS platform from URL patterns"""
        for ats, patterns in ATSDetector.ATS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return ats
        return None

    @staticmethod
    def detect_from_dom(page_content: str) -> Optional[str]:
        """Detect ATS platform from DOM content/fingerprints"""
        content_lower = page_content.lower()

        # Workday fingerprints
        if 'workday' in content_lower or 'wd-content' in content_lower:
            return 'workday'

        # Greenhouse fingerprints
        if 'greenhouse' in content_lower or 'gh_embedded' in content_lower:
            return 'greenhouse'

        # Lever fingerprints
        if 'lever' in content_lower or 'lever-application' in content_lower:
            return 'lever'

        # LinkedIn fingerprints
        if 'linkedin' in content_lower and 'jobs' in content_lower:
            return 'linkedin'

        return None

    @classmethod
    def detect(cls, url: str, page_content: Optional[str] = None) -> Optional[str]:
        """Combined detection using URL and DOM"""
        ats = cls.detect_from_url(url)
        if ats:
            return ats

        if page_content:
            ats = cls.detect_from_dom(page_content)
            if ats:
                return ats

        return None