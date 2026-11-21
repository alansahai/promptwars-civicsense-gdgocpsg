"""Secure image validation and decoding utility.

Validates image magic bytes, enforces a 300 KB file limit, and rejects
spoofed or uncompressed payloads.
"""

import base64
from typing import Final

MAX_IMAGE_BYTES: Final[int] = 307_200  # 300 KB limit

# Magic byte signatures for authorized web image formats
MAGIC_BYTES: Final[dict[str, bytes]] = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/webp": b"RIFF",  # WEBP format begins with RIFF header
}


def extract_base64_payload(data_url: str) -> tuple[str, str | None]:
    """Extract raw base64 string and declared mime type from data URL."""
    if "," in data_url:
        header, b64_str = data_url.split(",", 1)
        mime = None
        if "data:" in header and ";base64" in header:
            mime = header.replace("data:", "").replace(";base64", "").strip()
        return b64_str.strip(), mime
    return data_url.strip(), None


def validate_and_decode_image(data_url: str) -> tuple[bool, str, bytes | None]:
    """Validate image payload against size constraints and true magic byte headers."""
    if not data_url:
        return False, "Empty image data", None

    b64_str, _ = extract_base64_payload(data_url)

    try:
        raw_bytes = base64.b64decode(b64_str, validate=True)
    except Exception:
        return False, "Invalid base64 encoding", None

    if len(raw_bytes) > MAX_IMAGE_BYTES:
        return False, f"Image exceeds maximum size limit of 300 KB (received {len(raw_bytes) // 1024} KB)", None

    # Detect format via magic byte signatures
    detected_mime = None
    if raw_bytes.startswith(MAGIC_BYTES["image/jpeg"]):
        detected_mime = "image/jpeg"
    elif raw_bytes.startswith(MAGIC_BYTES["image/png"]):
        detected_mime = "image/png"
    elif raw_bytes.startswith(MAGIC_BYTES["image/webp"]) and b"WEBP" in raw_bytes[:16]:
        detected_mime = "image/webp"

    if not detected_mime:
        return False, "Unsupported image type. Only JPEG, PNG, or WebP files are allowed.", None

    return True, detected_mime, raw_bytes
