"""Vercel Serverless Function entrypoint.

Exposes the FastAPI ASGI application as `app`.
"""

from app.main import app

__all__ = ["app"]
