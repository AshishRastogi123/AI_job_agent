from playwright.sync_api import sync_playwright, Page, Browser
from typing import Dict, List, Optional, Tuple
import time
from config import HEADLESS

class BrowserAutomation:
    """Browser automation using Playwright for job application forms"""

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

    def navigate_to_job(self, url: str) -> str:
        """Navigate to job URL and return page content"""
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        self._dismiss_cookie_popup()
        return self.page.content()

    def _dismiss_cookie_popup(self):
        selectors = [
            'button:has-text("accept all")',
            'button:has-text("accept cookies")',
            'button:has-text("agree")',
            'button:has-text("allow all")',
            'button:has-text("ok")',
            'button:has-text("yes")',
            'button:has-text("accept")',
            'button:has-text("got it")',
        ]
        frames = [self.page] + list(self.page.frames)
        for frame in frames:
            for selector in selectors:
                try:
                    button = frame.query_selector(selector)
                    if button and button.is_visible():
                        button.click()
                        self.page.wait_for_timeout(500)
                        return
                except Exception:
                    continue

    def detect_form_fields(self) -> List[Dict]:
        """Detect all form fields on the page"""
        fields = []

        # Common selectors for different ATS platforms
        selectors = [
            'input[type="text"]',
            'input[type="email"]',
            'input[type="tel"]',
            'input[type="file"]',
            'textarea',
            'select',
            'input[type="radio"]',
            'input[type="checkbox"]'
        ]

        for selector in selectors:
            elements = self.page.query_selector_all(selector)
            for element in elements:
                field_info = self._get_field_info(element)
                if field_info:
                    fields.append(field_info)

        return fields

    def _get_field_info(self, element) -> Optional[Dict]:
        """Extract field information"""
        try:
            tag_name = element.evaluate('el => el.tagName.toLowerCase()')
            input_type = element.get_attribute('type') if tag_name == 'input' else None
            name = element.get_attribute('name') or element.get_attribute('id') or ''
            placeholder = element.get_attribute('placeholder') or ''
            label = self._find_label(element)

            return {
                'tag': tag_name,
                'type': input_type,
                'name': name.lower(),
                'placeholder': placeholder.lower(),
                'label': label.lower(),
                'required': element.get_attribute('required') is not None,
                'element': element
            }
        except Exception:
            return None

    def _find_label(self, element) -> str:
        """Find associated label for form element"""
        try:
            # Try to find label by 'for' attribute
            element_id = element.get_attribute('id')
            if element_id:
                label = self.page.query_selector(f'label[for="{element_id}"]')
                if label:
                    return label.inner_text().strip()

            # Try to find preceding label
            parent = element.query_selector('xpath=ancestor::div[1]')
            if parent:
                label = parent.query_selector('label')
                if label:
                    return label.inner_text().strip()

            return ''
        except Exception:
            return ''

    def fill_field(self, field: Dict, value: str) -> bool:
        """Fill a form field with given value"""
        try:
            element = field['element']

            if field['tag'] == 'select':
                element.select_option(value=value)
            elif field['tag'] == 'input' and field['type'] == 'file':
                # For file uploads, assume value is file path
                element.set_input_files(value)
            elif field['tag'] == 'input' and field['type'] == 'radio':
                element.check()
            elif field['tag'] == 'input' and field['type'] == 'checkbox':
                if value.lower() in ['yes', 'true', '1']:
                    element.check()
                else:
                    element.uncheck()
            else:
                element.fill(value)

            return True
        except Exception as e:
            print(f"Error filling field {field.get('name', 'unknown')}: {e}")
            return False

    def submit_form(self) -> bool:
        """Submit the job application form"""
        try:
            # Look for submit buttons
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Apply")',
                'button:has-text("Submit")',
                'button:has-text("Send Application")'
            ]

            for selector in submit_selectors:
                button = self.page.query_selector(selector)
                if button and button.is_visible():
                    button.click()
                    self.page.wait_for_load_state('networkidle')
                    return True

            return False
        except Exception as e:
            print(f"Error submitting form: {e}")
            return False

    def get_page_content(self) -> str:
        """Get current page content"""
        return self.page.content()

    def wait_for_timeout(self, seconds: int):
        """Wait for specified seconds"""
        time.sleep(seconds)