"""
Form Filling Engine
Intelligently fills out job application forms using Playwright
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import Page
from services.field_resolver import FieldResolver
from config import HEADLESS, BROWSER_TIMEOUT
import logging
import time
from typing import List, Dict

logger = logging.getLogger(__name__)


class FormFillingEngine:
    """Fill form fields intelligently"""
    
    def __init__(self, page: Page, user_id: int):
        self.page = page
        self.user_id = user_id
        self.field_resolver = FieldResolver(user_id)
        self.filled_fields = []
        self.unanswered_fields = []
    
    def detect_fields(self) -> List[Dict]:
        """Detect all form fields on the page"""
        fields = []
        
        selectors = [
            'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"])',
            'textarea',
            'select'
        ]
        
        frames = [self.page.main_frame] + [frame for frame in self.page.frames if frame != self.page.main_frame]
        for frame in frames:
            for selector in selectors:
                try:
                    elements = frame.query_selector_all(selector)
                    for element in elements:
                        field_info = self._extract_field_info(element, selector)
                        if field_info:
                            fields.append(field_info)
                except Exception as e:
                    logger.debug(f"Error detecting fields with selector {selector} in frame: {e}")
        
        logger.info(f"Detected {len(fields)} form fields")
        return fields
    
    def fill_forms(self, job_description: str = "") -> Dict:
        """
        Fill all detected form fields
        
        Returns:
            {
                'filled_count': int,
                'unanswered': list,
                'errors': list
            }
        """
        logger.info("Starting form filling process")
        fields = self.detect_fields()
        
        errors = []
        
        for field in fields:
            try:
                result = self.fill_field(field, job_description)
                
                if result.get('filled'):
                    self.filled_fields.append({
                        'label': field.get('label', field.get('name', '')),
                        'value': str(result.get('value', ''))
                    })
                else:
                    self.unanswered_fields.append({
                        'label': field.get('label', field.get('name', '')),
                        'type': field.get('type', 'unknown')
                    })
            
            except Exception as e:
                logger.error(f"Error filling field {field.get('label', 'unknown')}: {e}")
                errors.append({
                    'field': field,
                    'error': str(e)
                })
        
        return {
            'filled_count': len(self.filled_fields),
            'unanswered': self.unanswered_fields,
            'filled_fields_detail': self.filled_fields,
            'errors': errors
        }
    
    def fill_field(self, field: Dict, context: str = "") -> Dict:
        """Fill a single field"""
        field_type = field.get('type', 'text')
        field_label = field.get('label', field.get('name', ''))
        element = field.get('element')
        
        logger.debug(f"Filling field: {field_label} (type: {field_type})")
        
        # Resolve field value
        resolved = self.field_resolver.resolve(field_label, field_type, context)
        
        if not resolved.get('value'):
            if field_type == 'checkbox' and field.get('required'):
                logger.info(f"Defaulting required checkbox {field_label} to yes")
                resolved = {
                    'value': 'yes',
                    'confidence': 0.5,
                    'source': 'DEFAULT',
                    'reasoning': 'Required checkbox defaulted to yes'
                }
            else:
                logger.warning(f"Could not resolve field: {field_label}")
                return {'filled': False, 'reason': 'no_value'}
        
        # Fill based on field type
        try:
            if not element.is_visible() or not element.is_enabled():
                try:
                    element.wait_for_element_state('visible', timeout=BROWSER_TIMEOUT)
                    element.wait_for_element_state('enabled', timeout=BROWSER_TIMEOUT)
                except Exception:
                    logger.warning(f"Skipping invisible or disabled field: {field_label}")
                    return {'filled': False, 'reason': 'not_visible_or_enabled'}

            if field_type in ['text', 'email', 'tel', 'number', 'date', 'url']:
                try:
                    element.wait_for_element_state('visible', timeout=3000)
                    element.wait_for_element_state('enabled', timeout=3000)
                    element.wait_for_element_state('stable', timeout=3000)
                except Exception:
                    logger.debug(f"Stability wait failed for {field_label}, continuing with fill")
                element.fill(str(resolved['value']), force=True)
                logger.info(f"Filled {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            elif field_type == 'textarea':
                try:
                    element.wait_for_element_state('visible', timeout=3000)
                    element.wait_for_element_state('enabled', timeout=3000)
                    element.wait_for_element_state('stable', timeout=3000)
                except Exception:
                    logger.debug(f"Stability wait failed for textarea {field_label}, continuing with fill")
                element.fill(str(resolved['value']), force=True)
                logger.info(f"Filled textarea {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            elif field_type == 'select':
                self._fill_select(element, resolved['value'])
                logger.info(f"Selected {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            elif field_type == 'radio':
                self._fill_radio(element, resolved['value'])
                logger.info(f"Selected radio {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            elif field_type == 'checkbox':
                if resolved['value'].lower() in ['yes', 'true', '1']:
                    element.check()
                else:
                    element.uncheck()
                logger.info(f"Set checkbox {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            elif field_type == 'file':
                self._fill_file(element, field_label)
                logger.info(f"Uploaded file for {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            else:
                logger.warning(f"Unsupported field type: {field_type}")
                return {'filled': False, 'reason': 'unsupported_type'}
        
        except Exception as e:
            logger.error(f"Error filling field {field_label}: {e}")
            raise


    def _extract_field_info(self, element, selector: str) -> Dict:
        """Extract field information from element"""
        try:
            tag_name = element.evaluate('el => el.tagName.toLowerCase()')
            input_type = (element.get_attribute('type') or '').lower()
            if not input_type:
                input_type = tag_name
            if tag_name == 'textarea':
                input_type = 'textarea'
            if tag_name == 'select':
                input_type = 'select'
            name = element.get_attribute('name') or element.get_attribute('id') or ''
            placeholder = element.get_attribute('placeholder') or ''
            required = element.get_attribute('required') is not None
            
            # Resolve field label text
            label = self._get_element_label(element, name)
            
            # Skip hidden or invisible fields
            if not self._is_visible_element(element):
                return None
            if self._is_irrelevant_field(name, label):
                return None
            
            return {
                'tag': tag_name,
                'type': input_type,
                'name': name,
                'placeholder': placeholder,
                'label': label or name,
                'required': required,
                'visible': True,
                'element': element
            }
        
        except Exception as e:
            logger.debug(f"Error extracting field info: {e}")
            return None
    
    def _get_element_label(self, element, element_id: str = "") -> str:
        """Find associated label for element"""
        try:
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                return aria_label.strip()

            aria_labelledby = element.get_attribute('aria-labelledby')
            if aria_labelledby:
                labels = []
                for label_id in aria_labelledby.split():
                    label_elem = self.page.query_selector(f'#{label_id}')
                    if label_elem:
                        labels.append(label_elem.inner_text().strip())
                if labels:
                    return ' '.join(labels)

            if element_id:
                label_elem = self.page.query_selector(f'label[for="{element_id}"]')
                if label_elem:
                    text = label_elem.inner_text().strip()
                    if text:
                        return text

            label_text = element.evaluate(
                'el => { const label = el.closest("label"); return label ? label.innerText.trim() : ""; }'
            )
            if label_text:
                return label_text.strip()

            return ""
        except Exception as e:
            logger.debug(f"Error resolving element label: {e}")
            return ""

    def _is_visible_element(self, element) -> bool:
        try:
            if not element.is_visible() or not element.is_enabled():
                return False
            box = element.bounding_box()
            if not box or box['width'] == 0 or box['height'] == 0:
                return False
            style = element.evaluate(
                'el => ({ visibility: window.getComputedStyle(el).visibility, display: window.getComputedStyle(el).display, opacity: window.getComputedStyle(el).opacity })',
                element
            )
            if style.get('visibility') == 'hidden' or style.get('display') == 'none' or style.get('opacity') == '0':
                return False
            return True
        except Exception:
            return False

    def _is_irrelevant_field(self, name: str, label: str) -> bool:
        normalized = f"{name or ''} {label or ''}".lower()
        skip_keywords = [
            'cookie', 'cookies', 'privacy', 'terms', 'consent', 'optanon',
            'onetrust', 'vendor', 'performance', 'functional', 'targeting',
            'marketing', 'accept all', 'reject all', 'cookie preferences',
            'search…', 'search'
        ]
        for keyword in skip_keywords:
            if keyword in normalized:
                return True
        return False
    
    def _fill_select(self, element, value: str):
        """Fill select dropdown"""
        try:
            # Try to select by value
            element.select_option(value)
        except:
            # Try to select by label
            options = self.page.evaluate('el => Array.from(el.options).map(o => o.textContent)', element)
            for i, opt_text in enumerate(options):
                if value.lower() in opt_text.lower():
                    element.select_option(index=i)
                    return
            # If not found, select first non-empty option
            if len(options) > 1:
                element.select_option(index=1)
    
    def _fill_radio(self, element, value: str):
        """Fill radio button"""
        if value.lower() in ['yes', 'true', '1']:
            element.check()
        else:
            element.uncheck()
    
    def _fill_file(self, element, field_label: str):
        """Handle file upload"""
        from db.queries import get_user
        user = get_user(self.user_id)
        
        if not user or not user.resume_path:
            logger.warning(f"No resume path for user {self.user_id}")
            return
        
        resume_path = user.resume_path
        if os.path.exists(resume_path):
            element.set_input_files(resume_path)
            logger.info(f"Uploaded resume: {resume_path}")
        else:
            logger.warning(f"Resume file not found: {resume_path}")


def print_filled_fields(filled_fields):
    print("\n" + "="*60)
    print("FORM FILL SUMMARY")
    print("="*60)

    for field in filled_fields:
        print(f"\nField: {field['label']}")
        print(f"Answer: {field['value']}")

    print("\n" + "-"*60)
    print(f"Total Fields Filled: {len(filled_fields)}")
    print("="*60)
