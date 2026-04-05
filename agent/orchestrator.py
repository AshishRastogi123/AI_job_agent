from langgraph.graph import StateGraph, END
from typing import Optional, Dict, Any, List, TypedDict
from browser.automation import BrowserAutomation
from ats.detector import ATSDetector
from utils.field_mapper import FieldMapper
from utils.pdf_utils import save_pdf
from llm.resume_generator import generate_resume
from llm.cover_letter import generate_cover_letter
from db.queries import update_job_status, mark_job_applied, get_pending_jobs
from job_queue.manager import JobQueue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobApplicationState(TypedDict):
    """State for the job application workflow"""
    job_id: int
    job_url: str
    job_description: str
    ats_platform: str
    resume_content: str
    cover_letter: str
    resume_path: str
    cover_letter_path: str
    form_fields: List[Dict]
    unanswered_fields: List[str]
    user_id: int

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
        workflow = StateGraph(Dict[str, Any])

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

    def _fetch_job(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch next job from queue"""
        logger.info("Fetching next job from queue...")
        job = self.queue.get_next_job()
        if not job:
            # Get from DB if queue is empty
            pending_jobs = get_pending_jobs()
            if pending_jobs:
                job_id, job_url = pending_jobs[0]
                return {**state, "job_id": job_id, "job_url": job_url}
            else:
                raise ValueError("No jobs available")
        else:
            return {**state, "job_url": job}
        logger.info(f"Processing job: {state['job_url']}")
        return state

    def _extract_job_description(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract job description from the job page"""
        logger.info("Extracting job description...")
        job_description = ""
        with BrowserAutomation() as browser:
            content = browser.navigate_to_job(state["job_url"])
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
                        job_description = element.inner_text()
                        break
                except:
                    continue

            if not job_description:
                # Fallback to page title and meta description
                job_description = browser.page.title()

        logger.info(f"Extracted JD length: {len(job_description)}")
        return {**state, "job_description": job_description}

    def _generate_resume(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tailored resume"""
        logger.info("Generating tailored resume...")
        profile = self.field_mapper.profile
        resume_content = generate_resume(profile, state["job_description"])
        
        # Generate PDF and save
        filename = f"resume_{state['user_id']}_{state['job_id']}"
        resume_path = save_pdf(resume_content, filename, title="Resume")
        
        logger.info("Resume generated and PDF saved")
        return {**state, "resume_content": resume_content, "resume_path": resume_path}

    def _generate_cover_letter(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cover letter"""
        logger.info("Generating cover letter...")
        profile = self.field_mapper.profile
        cover_letter = generate_cover_letter(profile, state["job_description"])
        
        # Generate PDF and save
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cover_letter_{state['user_id']}_{timestamp}"
        cover_letter_path = save_pdf(cover_letter, filename, title="Cover Letter")
        
        logger.info("Cover letter generated and PDF saved")
        return {**state, "cover_letter": cover_letter, "cover_letter_path": cover_letter_path}

    def _detect_ats(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect ATS platform"""
        logger.info("Detecting ATS platform...")
        with BrowserAutomation() as browser:
            content = browser.navigate_to_job(state["job_url"])
            ats_platform = ATSDetector.detect(state["job_url"], content) or "unknown"
        logger.info(f"Detected ATS: {ats_platform}")
        return {**state, "ats_platform": ats_platform}

    def _open_browser(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Open browser and navigate to job"""
        logger.info("Opening browser...")
        # Browser is opened in fill_form step
        return state

    def _fill_form(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fill out the application form"""
        logger.info("Filling application form...")
        with BrowserAutomation() as browser:
            browser.navigate_to_job(state["job_url"])
            form_fields = browser.detect_form_fields()

            for field in form_fields:
                value = self.field_mapper.map_field(field, state.get("resume_path"), state.get("cover_letter_path"))
                if value:
                    success = browser.fill_field(field, value)
                    if not success:
                        logger.warning(f"Failed to fill field: {field.get('name', 'unknown')}")
                else:
                    logger.warning(f"Could not map field: {field.get('name', 'unknown')}")

            unanswered_fields = self.field_mapper.get_unanswered_fields(form_fields)

        logger.info(f"Form filling complete. Unanswered fields: {len(unanswered_fields)}")
        return {**state, "form_fields": form_fields, "unanswered_fields": unanswered_fields}

    def _submit_application(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Submit the application"""
        logger.info("Submitting application...")
        with BrowserAutomation() as browser:
            browser.navigate_to_job(state["job_url"])
            # Re-fill form if needed (simplified)
            success = browser.submit_form()
            if success:
                logger.info("Application submitted successfully")
                unanswered_fields = state["unanswered_fields"]
            else:
                logger.error("Failed to submit application")
                unanswered_fields = state["unanswered_fields"] + ["form_submission"]
        return {**state, "unanswered_fields": unanswered_fields}

    def _log_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Log the application result"""
        if state["unanswered_fields"]:
            update_job_status(
                state["job_id"],
                "failed",
                f"Unanswered fields: {', '.join(state['unanswered_fields'])}",
                state["unanswered_fields"]
            )
            logger.error(f"Application failed for job {state['job_id']}")
        else:
            mark_job_applied(state["job_id"])
            logger.info(f"Application successful for job {state['job_id']}")
        return state

    def run_application(self, job_url: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete job application workflow"""
        initial_state: Dict[str, Any] = {
            "job_id": 0,
            "job_url": job_url or "",
            "job_description": "",
            "ats_platform": "",
            "resume_content": "",
            "cover_letter": "",
            "resume_path": "",
            "cover_letter_path": "",
            "form_fields": [],
            "unanswered_fields": [],
            "user_id": self.user_id
        }

        if job_url:
            self.queue.add_job(job_url)

        try:
            final_state = self.workflow.invoke(initial_state)
            return {
                "success": len(final_state["unanswered_fields"]) == 0,
                "job_url": final_state["job_url"],
                "ats_platform": final_state["ats_platform"],
                "unanswered_fields": final_state["unanswered_fields"]
            }
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {"success": False, "error": str(e)}