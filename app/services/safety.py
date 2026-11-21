"""Input sanitization, prompt injection defenses, and safe text boundaries."""

import re
from typing import Final

# Regex pattern identifying common LLM prompt injection attempts
INJECTION_PATTERNS: Final[list[re.Pattern]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"dan\s+mode", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?secret", re.IGNORECASE),
    re.compile(r"developer\s+mode\s+output", re.IGNORECASE),
    re.compile(r"drop\s+table", re.IGNORECASE),
]


def strip_control_characters(text: str) -> str:
    """Remove invisible ASCII control characters while preserving valid newlines."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    """Scan text for potential prompt injection or jailbreak phrases."""
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)
    return False, None


def sanitize_user_text(text: str, max_length: int = 3000) -> str:
    """Sanitize, normalize whitespace, and constrain length of user-provided input."""
    if not text:
        return ""
    cleaned = strip_control_characters(text)
    # Neutralize HTML tags
    cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")
    # Trim to max length
    return cleaned[:max_length].strip()


def build_safe_prompt_envelope(user_description: str, address: str | None = None) -> str:
    """Delimit citizen text safely inside immutable XML boundary tags."""
    sanitized_desc = sanitize_user_text(user_description)
    sanitized_addr = sanitize_user_text(address or "Not provided", max_length=200)

    envelope = (
        "<report>\n"
        f"  <citizen_description>{sanitized_desc}</citizen_description>\n"
        f"  <reported_location>{sanitized_addr}</reported_location>\n"
        "</report>"
    )
    return envelope
