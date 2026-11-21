"""Main FastAPI application factory, middleware configuration, and routing."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin_routes import router as admin_router
from app.api.public_routes import router as public_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()
    if settings.is_production and not settings.demo_mode:
        if settings.admin_password == "civic-demo-2026":
            raise RuntimeError(
                "CRITICAL: Default admin password must be changed in live production environment!"
            )
    yield


app = FastAPI(
    title="CivicResolve API",
    description="AI-Powered Municipal Citizen Grievance Management and Resolution Platform",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

# 1. GZip Compression for efficient data transfer
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. CORS Middleware
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# 3. Security Headers and Request Size Guard Middleware
@app.middleware("http")
async def security_and_size_guard(request: Request, call_next):
    # Guard against oversized payloads (> 600 KB)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 614_400:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Payload exceeds maximum allowed size of 600 KB"},
        )

    response: Response = await call_next(request)

    # Inject hardening security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none';"
    )

    # Disable caching on admin routes
    if request.url.path.startswith("/api/admin"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

    return response


# 4. Custom validation error formatting
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request schema",
            "errors": [
                {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
                for err in exc.errors()
            ],
        },
    )


# 5. Mount API Routers
app.include_router(public_router)
app.include_router(admin_router)

# 6. Static files mount for local development
public_dir = Path(__file__).resolve().parent.parent / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="public")
