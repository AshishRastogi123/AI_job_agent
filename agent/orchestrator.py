from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from browser.automation import BrowserAutomation
from ats.detector import ATSDetector
from utils.field_mapper import FieldMapper
from llm.resume_generator import generate_resume
from llm.cover_letter import generate_cover_letter
from db.queries import update_job_status, mark_job_applied, get_pending_jobs
from queue.manager import JobQueue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobApplicationState:
    """State for the job application workflow"""
    def __init__(self):
        self.job_id: int = 0
        self.job_url: str = ""
        self.job_description: str = ""
        self.ats_platform: str = ""
        self.resume_content: str = ""
        self.cover_letter: str = ""
        self.form_fields: List[Dict] = []
        self.unanswered_fields: List[str] = []
        self.user_id: int = 1  # Default user for demo

class JobApplicationAgent:
    """LangGraph-based agent for autonomous job applications"""

    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.field_mapper = FieldMapper(user_id)
        self.queue = JobQueue()

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(JobApplicationState)

        # Add nodes
        workflow.add_node("fetch_job", self._fetch_job)
        workflow.add_node("extract_jd", self._extract_job_description)
        workflow.add_node("generate_resume", self._generate_resume)
        workflow.add_node("generate_cover_letter", self._generate_cover_letter)
        workflow.add_node("detect_ats", self._detect_ats)
        workflow.add_node("open_browser", self._open_browser)
        workflow.add_node("fill_form", self._fill_form)
        workflow.add_node("submit_application", self._submit_application)
        workflow.add_node("log_result", self._log_result)

        # Define edges
        workflow.set_entry_point("fetch_job")
        workflow.add_edge("fetch_job", "extract_jd")
        workflow.add_edge("extract_jd", "generate_resume")
        workflow.add_edge("generate_resume", "generate_cover_letter")
        workflow.add_edge("generate_cover_letter", "detect_ats")
        workflow.add_edge("detect_ats", "open_browser")
        workflow.add_edge("open_browser", "fill_form")
        workflow.add_edge("fill_form", "submit_application")
        workflow.add_edge("submit_application", "log_result")
        workflow.add_edge("log_result", END)

        return workflow.compile()

    def _fetch_job(self, state: JobApplicationState) -> JobApplicationState:
        """Fetch next job from queue"""
        logger.info("Fetching next job from queue...")
        job = self.queue.get_next_job()
        if not job:
            # Get from DB if queue is empty
            pending_jobs = get_pending_jobs()
            if pending_jobs:
                state.job_id, state.job_url = pending_jobs[0]
            else:
                raise ValueError("No jobs available")
        else:
            state.job_url = job
        logger.info(f"Processing job: {state.job_url}")
        return state

    def _extract_job_description(self, state: JobApplicationState) -> JobApplicationState:
        """Extract job description from the job page"""
        logger.info("Extracting job description...")
        with BrowserAutomation() as browser:
            content = browser.navigate_to_job(state.job_url)
            # Simple extraction - in production, use more sophisticated parsing
            # Look for common JD containers
            jd_selectors = [
                '[data-testid*="job-description"]',
                '[class*="job-description"]',
                '[id*="job-description"]',
                'div[class*="description"]',
                'section[class*="job"]'
            ]

            for selector in jd_selectors:
                try:
                    element = browser.page.query_selector(selector)
                    if element:
                        state.job_description = element.inner_text()
                        break
                except:
                    continue

            if not state.job_description:
                # Fallback to page title and meta description
                state.job_description = browser.page.title()

        logger.info(f"Extracted JD length: {len(state.job_description)}")
        return state

    def _generate_resume(self, state: JobApplicationState) -> JobApplicationState:
        """Generate tailored resume"""
        logger.info("Generating tailored resume...")
        profile = self.field_mapper.profile
        state.resume_content = generate_resume(profile, state.job_description)
        logger.info("Resume generated")
        return state

    def _generate_cover_letter(self, state: JobApplicationState) -> JobApplicationState:
        """Generate cover letter"""
        logger.info("Generating cover letter...")
        profile = self.field_mapper.profile
        state.cover_letter = generate_cover_letter(profile, state.job_description)
        logger.info("Cover letter generated")
        return state

    def _detect_ats(self, state: JobApplicationState) -> JobApplicationState:
        """Detect ATS platform"""
        logger.info("Detecting ATS platform...")
        with BrowserAutomation() as browser:
            content = browser.navigate_to_job(state.job_url)
            state.ats_platform = ATSDetector.detect(state.job_url, content) or "unknown"
        logger.info(f"Detected ATS: {state.ats_platform}")
        return state

    def _open_browser(self, state: JobApplicationState) -> JobApplicationState:
        """Open browser and navigate to job"""
        logger.info("Opening browser...")
        # Browser is opened in fill_form step
        return state

    def _fill_form(self, state: JobApplicationState) -> JobApplicationState:
        """Fill out the application form"""
        logger.info("Filling application form...")
        with BrowserAutomation() as browser:
            browser.navigate_to_job(state.job_url)
            state.form_fields = browser.detect_form_fields()

            for field in state.form_fields:
                value = self.field_mapper.map_field(field)
                if value:
                    success = browser.fill_field(field, value)
                    if not success:
                        logger.warning(f"Failed to fill field: {field.get('name', 'unknown')}")
                else:
                    logger.warning(f"Could not map field: {field.get('name', 'unknown')}")

            state.unanswered_fields = self.field_mapper.get_unanswered_fields(state.form_fields)

        logger.info(f"Form filling complete. Unanswered fields: {len(state.unanswered_fields)}")
        return state

    def _submit_application(self, state: JobApplicationState) -> JobApplicationState:
        """Submit the application"""
        logger.info("Submitting application...")
        with BrowserAutomation() as browser:
            browser.navigate_to_job(state.job_url)
            # Re-fill form if needed (simplified)
            success = browser.submit_form()
            if success:
                logger.info("Application submitted successfully")
            else:
                logger.error("Failed to submit application")
                state.unanswered_fields.append("form_submission")
        return state

    def _log_result(self, state: JobApplicationState) -> JobApplicationState:
        """Log the application result"""
        if state.unanswered_fields:
            update_job_status(
                state.job_id,
                "failed",
                f"Unanswered fields: {', '.join(state.unanswered_fields)}",
                state.unanswered_fields
            )
            logger.error(f"Application failed for job {state.job_id}")
        else:
            mark_job_applied(state.job_id)
            logger.info(f"Application successful for job {state.job_id}")
        return state

    def run_application(self, job_url: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete job application workflow"""
        initial_state = JobApplicationState()
        initial_state.user_id = self.user_id

        if job_url:
            self.queue.add_job(job_url)
            initial_state.job_url = job_url

        try:
            final_state = self.workflow.invoke(initial_state)
            return {
                "success": len(final_state.unanswered_fields) == 0,
                "job_url": final_state.job_url,
                "ats_platform": final_state.ats_platform,
                "unanswered_fields": final_state.unanswered_fields
            }
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {"success": False, "error": str(e)}