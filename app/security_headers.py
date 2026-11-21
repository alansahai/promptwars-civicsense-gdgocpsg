"""Single source of truth for application security headers and CSP policy.

Defines HTTP headers and strict Content Security Policy directives
used across FastAPI middleware and verified against vercel.json.
"""

from typing import Final

CONTENT_SECURITY_POLICY: Final[str] = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none';"
)

BASE_SECURITY_HEADERS: Final[dict[str, str]] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(self)",
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
}
