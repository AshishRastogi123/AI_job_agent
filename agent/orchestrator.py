"""
Complete AI Job Application Agent Orchestrator
Handles end-to-end job application workflow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from services.jd_extractor import JDExtractor
from services.field_resolver import FieldResolver
from services.form_filler import FormFillingEngine, print_filled_fields
from browser.automation import BrowserAutomation
from ats.detector import ATSDetector
from llm.resume_generator import generate_resume
from llm.cover_letter import generate_cover_letter
from db.queries import (
    get_user_profile, update_job_status, update_job_ats_platform,
    mark_job_applied, save_unanswered_fields, log_application_step,
    get_pending_jobs
)
from utils.logging_config import get_logger
from job_queue.manager import JobQueue
from utils.pdf_utils import save_text_pdf
import time

logger = get_logger(__name__)


class JobApplicationAgent:
    """Complete orchestrator for autonomous job applications"""
    
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.queue = JobQueue()
        self.user_profile = get_user_profile(user_id)
        
        if not self.user_profile:
            raise ValueError(f"User {user_id} not found")
        
        logger.info(f"Initialized agent for user: {self.user_profile['name']}")
    
    def run_application(self, job_url: str = None) -> Dict[str, Any]:
        """
        Run complete application workflow for a job
        
        Returns:
            {
                'success': bool,
                'job_id': int,
                'job_url': str,
                'ats_platform': str,
                'status': str,
                'filled_fields': int,
                'unanswered_fields': list,
                'errors': list,
                'message': str
            }
        """
        result = {
            'success': False,
            'job_id': None,
            'job_url': job_url,
            'ats_platform': None,
            'status': 'failed',
            'filled_fields': 0,
            'unanswered_fields': [],
            'errors': [],
            'resume_path': None,
            'cover_letter_path': None,
            'message': ''
        }
        
        try:
            # Step 1: Fetch or use provided job URL
            if not job_url:
                pending_jobs = get_pending_jobs(limit=1)
                if not pending_jobs:
                    result['message'] = 'No pending jobs available'
                    return result
                job_id, job_url = pending_jobs[0]
                result['job_url'] = job_url
            else:
                job_id = None
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting job application for: {job_url}")
            logger.info(f"{'='*60}")
            
            # Step 2: Extract Job Description
            logger.info("\n[STEP 1] Extracting job description...")
            jd, jd_success = self._extract_job_description(job_url)
            
            if not jd_success:
                result['message'] = 'Failed to extract job description after retries'
                result['status'] = 'failed'
                result['errors'].append('JD extraction failed')
                if job_id:
                    update_job_status(job_id, 'failed', result['message'])
                    log_application_step(job_id, self.user_id, 'extract_jd', 'failure', result['message'])
                return result
            
            if job_id:
                log_application_step(job_id, self.user_id, 'extract_jd', 'success', f'Extracted {len(jd)} characters')
            
            logger.info(f"✓ Extracted {len(jd)} characters of job description")
            
            # Step 3: Detect ATS Platform
            logger.info("\n[STEP 2] Detecting ATS platform...")
            ats_platform = self._detect_ats_platform(job_url)
            result['ats_platform'] = ats_platform
            logger.info(f"✓ Detected ATS: {ats_platform}")
            
            if job_id:
                update_job_ats_platform(job_id, ats_platform)
                log_application_step(job_id, self.user_id, 'detect_ats', 'success', f'Detected: {ats_platform}')
            
            # Step 4: Generate Tailored Resume
            logger.info("\n[STEP 3] Generating tailored resume...")
            resume_content = self._generate_resume(jd)
            logger.info(f"✓ Generated resume ({len(resume_content)} characters)")
            
            if resume_content:
                resume_path = save_text_pdf(resume_content, 'resume', job_id, title='Resume')
                result['resume_path'] = resume_path
                logger.info(f"Resume saved successfully at: {resume_path}")
            else:
                logger.warning('Resume generation returned empty content; skipping PDF save')
            
            if job_id:
                log_application_step(job_id, self.user_id, 'generate_resume', 'success')
            
            # Step 5: Generate Cover Letter
            logger.info("\n[STEP 4] Generating cover letter...")
            cover_letter = self._generate_cover_letter(jd)
            logger.info(f"✓ Generated cover letter ({len(cover_letter)} characters)")
            
            if cover_letter:
                cover_letter_path = save_text_pdf(cover_letter, 'cover_letter', job_id, title='Cover Letter')
                result['cover_letter_path'] = cover_letter_path
                logger.info(f"Cover letter saved successfully at: {cover_letter_path}")
            else:
                logger.warning('Cover letter generation returned empty content; skipping PDF save')
            
            if job_id:
                log_application_step(job_id, self.user_id, 'generate_cover_letter', 'success')
            
            # Step 6: Open Browser and Fill Form
            logger.info("\n[STEP 5] Opening browser and filling form...")
            form_result = self._fill_application_form(job_url, jd)
            
            result['filled_fields'] = form_result.get('filled_count', 0)
            result['unanswered_fields'] = form_result.get('unanswered', [])
            result['errors'].extend(form_result.get('errors', []))
            if form_result.get('filled_fields_detail'):
                print_filled_fields(form_result.get('filled_fields_detail', []))
            
            if job_id:
                log_application_step(
                    job_id, self.user_id, 'fill_form', 'success',
                    f"Filled {result['filled_fields']} fields"
                )
            
            logger.info(f"✓ Filled {result['filled_fields']} form fields")
            if result['unanswered_fields']:
                logger.warning(f"⚠ {len(result['unanswered_fields'])} unanswered fields")
            
            # Step 7: Submit Application
            logger.info("\n[STEP 6] Submitting application...")
            submit_success = self._submit_application(job_url)
            
            if submit_success:
                logger.info("✓ Application submitted successfully")
                result['success'] = True
                result['status'] = 'applied'
                result['message'] = 'Application submitted successfully'
                
                if job_id:
                    mark_job_applied(job_id)
                    save_unanswered_fields(job_id, result['unanswered_fields'])
                    log_application_step(job_id, self.user_id, 'submit_application', 'success')
            else:
                logger.error("✗ Failed to submit application")
                result['status'] = 'failed'
                result['message'] = 'Failed to submit application'
                result['errors'].append('Submission failed')
                
                if job_id:
                    update_job_status(job_id, 'failed', 'Submission failed')
                    log_application_step(job_id, self.user_id, 'submit_application', 'failure')
            
            # Step 8: Log Results
            logger.info("\n[STEP 7] Logging results...")
            logger.info(f"\n{'='*60}")
            logger.info(f"Final Status: {result['status'].upper()}")
            logger.info(f"Filled Fields: {result['filled_fields']}")
            logger.info(f"Unanswered: {len(result['unanswered_fields'])}")
            logger.info(f"{'='*60}\n")
            
            return result
        
        except Exception as e:
            logger.error(f"Unexpected error during application: {e}", exc_info=True)
            result['status'] = 'failed'
            result['message'] = f'Unexpected error: {str(e)}'
            result['errors'].append(str(e))
            return result
    
    def _extract_job_description(self, job_url: str) -> tuple:
        """Extract job description from URL"""
        try:
            with JDExtractor() as extractor:
                jd, success = extractor.extract(job_url)
                return jd, success
        except Exception as e:
            logger.error(f"Error extracting JD: {e}")
            return "", False
    
    def _detect_ats_platform(self, job_url: str) -> str:
        """Detect ATS platform using URL and HTML"""
        try:
            # Try URL detection first
            ats = ATSDetector.detect_from_url(job_url)
            if ats:
                return ats
            
            # Try DOM detection
            try:
                with BrowserAutomation() as browser:
                    content = browser.navigate_to_job(job_url)
                    ats = ATSDetector.detect_from_dom(content)
                    return ats or "unknown"
            except:
                return "unknown"
        
        except Exception as e:
            logger.error(f"Error detecting ATS: {e}")
            return "unknown"
    
    def _generate_resume(self, job_description: str) -> str:
        """Generate tailored resume"""
        try:
            resume = generate_resume(self.user_profile, job_description)
            return resume
        except Exception as e:
            logger.error(f"Error generating resume: {e}")
            return ""
    
    def _generate_cover_letter(self, job_description: str) -> str:
        """Generate cover letter"""
        try:
            cover_letter = generate_cover_letter(self.user_profile, job_description)
            return cover_letter
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return ""
    
    def _fill_application_form(self, job_url: str, jd: str) -> Dict[str, Any]:
        """Fill out application form"""
        try:
            with BrowserAutomation() as browser:
                browser.navigate_to_job(job_url)
                
                # Create form filler
                filler = FormFillingEngine(browser.page, self.user_id)
                
                # Fill forms
                result = filler.fill_forms(jd)
                
                return result
        
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return {
                'filled_count': 0,
                'unanswered': [],
                'errors': [str(e)]
            }
    
    def _submit_application(self, job_url: str) -> bool:
        """Submit application"""
        try:
            with BrowserAutomation() as browser:
                browser.navigate_to_job(job_url)
                
                # Look for submit button
                submit_buttons = [
                    'button[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    'button:has-text("Send")',
                    '[data-testid*="submit"]',
                    '[class*="submit"]'
                ]
                
                for selector in submit_buttons:
                    try:
                        button = browser.page.query_selector(selector)
                        if button:
                            logger.debug(f"Found submit button: {selector}")
                            button.click()
                            time.sleep(2)  # Wait for submission
                            return True
                    except:
                        continue
                
                logger.warning("Could not find submit button")
                return False
        
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False


def main():
    """Main entry point for CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Job Application Agent')
    parser.add_argument('--job-url', help='Single job URL to process')
    parser.add_argument('--user-id', type=int, default=1, help='User ID (default: 1)')
    parser.add_argument('--add-jobs', nargs='+', help='Add job URLs to queue')
    parser.add_argument('--process-queue', action='store_true', help='Process all jobs in queue')
    
    args = parser.parse_args()
    
    try:
        agent = JobApplicationAgent(user_id=args.user_id)
        queue = JobQueue()
        
        if args.add_jobs:
            for url in args.add_jobs:
                queue.add_job(url)
                print(f"Added job to queue: {url}")
        
        if args.job_url:
            result = agent.run_application(args.job_url)
            print(f"\nResult: {result}")
        
        elif args.process_queue:
            while queue.get_queue_size() > 0:
                result = agent.run_application()
                print(f"\nProcessed: {result['message']}")
                time.sleep(2)  # Between applications
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
