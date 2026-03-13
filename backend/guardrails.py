"""
Input validation guardrails to prevent prompt injection.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_user_input(text: Optional[str]) -> str:
    """Remove potential prompt injection attempts."""
    if text is None:
        return ""

    dangerous_patterns = [
        "ignore previous instructions",
        "disregard all prior",
        "forget everything",
        "new instructions:",
        "system:",
        "assistant:",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            logger.warning(f"Potential prompt injection detected: {pattern}")
            return "[INVALID INPUT DETECTED]"

    return text


def truncate_response(text: str, max_length: int = 50000) -> str:
    """Ensure responses don't exceed reasonable size."""
    if len(text) > max_length:
        logger.warning(f"Response truncated from {len(text)} to {max_length} characters")
        return text[:max_length] + "\n\n[Response truncated due to length]"
    return text
