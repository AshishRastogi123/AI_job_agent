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
            'input[type="text"]',
            'input[type="email"]',
            'input[type="tel"]',
            'input[type="number"]',
            'input[type="date"]',
            'input[type="file"]',
            'input[type="url"]',
            'textarea',
            'select',
            'input[type="radio"]',
            'input[type="checkbox"]'
        ]
        
        for selector in selectors:
            try:
                elements = self.page.query_selector_all(selector)
                for element in elements:
                    field_info = self._extract_field_info(element, selector)
                    if field_info:
                        fields.append(field_info)
            except Exception as e:
                logger.debug(f"Error detecting fields with selector {selector}: {e}")
        
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
            if field_type in ['text', 'email', 'tel', 'number', 'date', 'url']:
                element.fill(str(resolved['value']))
                logger.info(f"Filled {field_label}: {resolved['source']}")
                return {'filled': True, 'source': resolved['source'], 'value': resolved['value']}
            
            elif field_type == 'textarea':
                element.fill(str(resolved['value']))
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
            input_type = element.get_attribute('type') or selector.split('"')[1]
            name = element.get_attribute('name') or element.get_attribute('id') or ''
            placeholder = element.get_attribute('placeholder') or ''
            required = element.get_attribute('required') is not None
            
            # Try to find label
            label = self._find_label(element, name)
            
            # Skip hidden fields
            if element.get_attribute('style') and 'display:none' in element.get_attribute('style'):
                return None
            
            return {
                'tag': tag_name,
                'type': input_type,
                'name': name,
                'placeholder': placeholder,
                'label': label or name,
                'required': required,
                'element': element
            }
        
        except Exception as e:
            logger.debug(f"Error extracting field info: {e}")
            return None
    
    def _find_label(self, element, element_id: str = "") -> str:
        """Find associated label for element"""
        try:
            # Try label with for attribute
            if element_id:
                label_elem = self.page.query_selector(f'label[for="{element_id}"]')
                if label_elem:
                    return label_elem.inner_text().strip()
            
            # Try parent label
            parent = self.page.evaluate('el => el.closest("label")', element)
            if parent:
                return parent.inner_text().strip()
            
            return ""
        
        except:
            return ""
    
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
