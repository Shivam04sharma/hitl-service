"""Sensitive data detection utility."""

import re
from typing import List, Dict

# Regex patterns for common sensitive data
PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "api_key": r'\b(?:sk|pk)[-_][a-zA-Z0-9]{20,}\b',
    "password": r'(?i)(?:password|passwd|pwd)[\s:=]+[^\s]{6,}',
}


def detect_sensitive_data(text: str) -> Dict[str, List[str]]:
    """Detect sensitive data patterns in text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dict with detected pattern types and matched values
    """
    detected = {}
    
    for pattern_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            # For phone numbers, join tuples
            if pattern_type == "phone" and matches and isinstance(matches[0], tuple):
                matches = [f"({m[0]}) {m[1]}-{m[2]}" for m in matches]
            detected[pattern_type] = matches
    
    return detected


def mask_sensitive_data(text: str) -> str:
    """Mask sensitive data in text.
    
    Args:
        text: Input text
        
    Returns:
        Text with sensitive data masked
    """
    masked = text
    
    for pattern_type, pattern in PATTERNS.items():
        if pattern_type == "email":
            masked = re.sub(pattern, "[EMAIL_REDACTED]", masked)
        elif pattern_type == "phone":
            masked = re.sub(pattern, "[PHONE_REDACTED]", masked)
        elif pattern_type == "ssn":
            masked = re.sub(pattern, "[SSN_REDACTED]", masked)
        elif pattern_type == "credit_card":
            masked = re.sub(pattern, "[CARD_REDACTED]", masked)
        elif pattern_type == "api_key":
            masked = re.sub(pattern, "[API_KEY_REDACTED]", masked)
        elif pattern_type == "password":
            masked = re.sub(pattern, "[PASSWORD_REDACTED]", masked)
    
    return masked
