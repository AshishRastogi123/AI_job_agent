import time
from typing import Optional, Dict
from config import HITL_TIMEOUT
from db.queries import save_custom_answer

class HITLManager:
    """Human-in-the-Loop manager for uncertain form fields"""

    def __init__(self, user_id: int):
        self.user_id = user_id

    def request_human_input(self, field_name: str, field_info: Dict) -> Optional[str]:
        """
        Request human input for a field.
        In a real implementation, this would integrate with a UI or messaging system.
        For now, it waits for console input.
        """
        print(f"\n🤖 Need human input for field: {field_name}")
        print(f"Field info: {field_info}")
        print(f"You have {HITL_TIMEOUT} seconds to respond...")

        # In production, this would be async with proper UI integration
        # For demo purposes, we'll use console input with timeout
        try:
            import msvcrt  # Windows-specific for timeout input
            start_time = time.time()
            user_input = ""

            print("Enter value (or press Enter to skip): ", end="", flush=True)

            while time.time() - start_time < HITL_TIMEOUT:
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    if char == b'\r':  # Enter key
                        break
                    elif char == b'\x08':  # Backspace
                        user_input = user_input[:-1]
                        print('\b \b', end='', flush=True)
                    else:
                        char_str = char.decode('utf-8', errors='ignore')
                        user_input += char_str
                        print(char_str, end='', flush=True)
                time.sleep(0.1)

            print()  # New line

            if user_input.strip():
                # Save to database for future use
                save_custom_answer(self.user_id, field_name, user_input.strip())
                return user_input.strip()
            else:
                print("No input received within timeout.")
                return None

        except ImportError:
            # Fallback for non-Windows systems
            print("Enter value (timeout in 30s): ", end="", flush=True)
            import select
            import sys

            if select.select([sys.stdin], [], [], HITL_TIMEOUT)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input:
                    save_custom_answer(self.user_id, field_name, user_input)
                    return user_input

            print("Timeout - no input received.")
            return None

    def should_fallback_to_hitl(self, field_name: str, confidence_score: float = 0.0) -> bool:
        """
        Determine if we should fallback to HITL based on field name and confidence.
        In production, this could use ML models to determine uncertainty.
        """
        # Always fallback for sensitive fields
        sensitive_fields = [
            'ssn', 'social_security', 'salary', 'compensation',
            'criminal', 'background', 'references'
        ]

        if any(keyword in field_name.lower() for keyword in sensitive_fields):
            return True

        # Fallback if confidence is low (placeholder for future ML integration)
        return confidence_score < 0.7