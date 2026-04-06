"""
Job Description Extraction Service
Extracts job descriptions from job pages using Playwright with validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from config import HEADLESS, BROWSER_TIMEOUT, MAX_RETRIES
import logging
import re

logger = logging.getLogger(__name__)


class JDExtractor:
    """Extract job description from a job URL"""
    
    # Common selectors for job description content
    JD_SELECTORS = [
        '[data-testid*="job-description"]',
        '[class*="job-description"]',
        '[id*="job-description"]',
        '[data-qa*="job-description"]',
        'div[class*="description"]',
        'section[class*="job"]',
        '[data-qa*="JobDescription"]',
        'div[class*="job-details"]',
        'div[class*="description-section"]',
        '[class*="posting-content"]',
        '[class*="jobDescription"]',
        'main',
        'article'
    ]
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=HEADLESS)
        self.page = self.browser.new_page()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def extract(self, url: str, retries: int = 0) -> tuple[str, bool]:
        """
        Extract job description from URL
        Returns: (job_description, success)
        """
        if retries > MAX_RETRIES:
            logger.error(f"Max retries ({MAX_RETRIES}) exceeded for {url}")
            return "", False
        
        try:
            logger.info(f"Extracting JD from: {url}")
            self.page.goto(url, timeout=BROWSER_TIMEOUT)
            self.page.wait_for_load_state('networkidle', timeout=BROWSER_TIMEOUT)
            
            # Get raw content
            content = self.page.content()
            jd = self._extract_from_content(content)
            
            # Validate minimum length
            if len(jd.strip()) < 300:
                logger.warning(f"JD too short ({len(jd)} chars), retrying...")
                return self.extract(url, retries + 1)
            
            logger.info(f"Successfully extracted {len(jd)} characters of JD")
            return jd, True
            
        except Exception as e:
            logger.warning(f"Extraction failed (attempt {retries + 1}/{MAX_RETRIES + 1}): {e}")
            return self.extract(url, retries + 1)
    
    def _extract_from_content(self, html: str) -> str:
        """Extract text from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style tags
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Try specific selectors first
        for selector in self.JD_SELECTORS:
            try:
                elements = soup.select(selector)
                if elements:
                    text_parts = [elem.get_text(strip=True) for elem in elements]
                    full_text = "\n".join(text_parts)
                    
                    if len(full_text.strip()) > 300:
                        logger.debug(f"Found JD using selector: {selector}")
                        return self._clean_text(full_text)
            except:
                continue
        
        # Fallback: try to extract body content, removing common noise
        for nav in soup.find_all(['nav', 'header', 'footer']):
            nav.decompose()
        
        # Get remaining text
        text = soup.get_text(separator='\n', strip=True)
        
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common footer patterns
        patterns = [
            r'Apply now.*$',
            r'Share job.*$',
            r'Report job.*$',
            r'Subscribe to.*$',
            r'(Follow|Like|Share|Cookie|Privacy|Terms).*$'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text.strip()
