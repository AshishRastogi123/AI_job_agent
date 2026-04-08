"""
Human-in-the-Loop manager for handling uncertain form fields
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
from typing import Optional, Dict
from config import HITL_TIMEOUT, HITL_ENABLED
from db.queries import save_custom_answer
from utils.logging_config import get_logger

logger = get_logger(__name__)


class HITLManager:
    """Human-in-the-Loop manager for uncertain form fields"""

    def __init__(self, user_id: int):
        self.user_id = user_id

    def request_human_input(self, field_name: str, field_info: Dict) -> Optional[str]:
        """
        Request human input for a field with timeout
        
        Args:
            field_name: Field label
            field_info: Field metadata (type, llm_suggestion, context)
        
        Returns:
            User input or None if timeout/skipped
        """
        if not HITL_ENABLED:
            return None
        
        print(f"\n{'='*60}")
        print(f"🤖 HUMAN INPUT REQUIRED")
        print(f"{'='*60}")
        print(f"Field: {field_name}")
        print(f"Type: {field_info.get('type', 'unknown')}")
        
        if field_info.get('llm_suggestion'):
            print(f"LLM Suggestion: {field_info['llm_suggestion']}")
        
        if field_info.get('context'):
            print(f"Context: {field_info['context'][:100]}...")
        
        print(f"\nTimeout: {HITL_TIMEOUT} seconds")
        print(f"{'='*60}")
        
        try:
            import signal
            
            class TimeoutException(Exception):
                pass
            
            def timeout_handler(signum, frame):
                raise TimeoutException()
            
            # Set timeout handler (Unix/Linux only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(HITL_TIMEOUT)
                
                user_input = input("Enter value (or press Ctrl+C to skip): ").strip()
                
                signal.alarm(0)  # Cancel alarm
                
                if user_input:
                    save_custom_answer(self.user_id, field_name, user_input)
                    logger.info(f"User provided input for {field_name}")
                    return user_input
            
            except (TimeoutException, AttributeError):
                # Timeout or not on Unix (signal not available on Windows)
                # Try Windows-specific approach
                if sys.platform == 'win32':
                    return self._windows_timeout_input()
                else:
                    logger.warning(f"Timeout waiting for input on {field_name}")
                    return None
        
        except KeyboardInterrupt:
            logger.info(f"User skipped {field_name}")
            return None
        except Exception as e:
            logger.warning(f"Error during HITL: {e}")
            return None
    
    def _windows_timeout_input(self) -> Optional[str]:
        """Windows-specific timeout input"""
        result = {'value': None}
        
        def input_thread():
            result['value'] = input("Enter value: ").strip()
        
        thread = threading.Thread(target=input_thread, daemon=True)
        thread.start()
        thread.join(timeout=HITL_TIMEOUT)
        
        if not thread.is_alive():
            return result['value']
        else:
            print("No input received within timeout.")
            return None

    def should_fallback_to_hitl(self, field_name: str, confidence_score: float = 0.0) -> bool:
        """
        Determine if we should fallback to HITL based on field name and confidence.
        In production, this could use ML models to determine uncertainty.
        """
        # Do not fallback to HITL for demographic or sensitive fields
        sensitive_fields = [
            'ssn', 'social_security', 'salary', 'compensation',
            'criminal', 'background', 'references', 'gender', 'hispanic', 'latino',
            'veteran', 'disability', 'race', 'ethnicity', 'citizenship', 'employment status', 'age'
        ]

        if any(keyword in field_name.lower() for keyword in sensitive_fields):
            return False

        # Fallback if confidence is low (placeholder for future ML integration)
        return confidence_score < 0.7