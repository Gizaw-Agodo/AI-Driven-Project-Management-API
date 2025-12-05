from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api.middleware import LoggingMiddleware, RateLimitMiddleware, RequestIDMiddleware, TimingMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.middleware.error_handlers import register_exception_handlers
from app.api.v1.api import api_router
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# 🎓 STEP 1: Setup Logging
setup_logging(
    level="DEBUG" if settings.DEBUG else "INFO",
    json_logs=not settings.DEBUG
)

# 🎓 STEP 2: Create FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Driven Project Management API",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
    openapi_url="/api/openapi.json"  # OpenAPI schema
)

# Protects against Host header attacks
if not settings.DEBUG: 
    app.add_middleware(TrustedHostMiddleware, allowed_hosts = [settings.TRUSTED_HOSTS])

# Must be before authentication middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# GZIP COMPRESSION (Performance)
app.add_middleware(GZipMiddleware, minimum_size = 1000)

# REQUEST ID (Tracing - Early)
app.add_middleware(RequestIDMiddleware)

# TIMING (Performance Monitoring)
app.add_middleware( TimingMiddleware, slow_request_threshold=1.0 )

# RATE LIMITING (Security & Resource Protection)
if not settings.DEBUG:
    app.add_middleware(RateLimitMiddleware, request_per_minute=60, request_per_hour=1000)

# LOGGING (Observability)
app.add_middleware(LoggingMiddleware)

# Register Exception Handlers
register_exception_handlers(app)

# Include API Routes
app.include_router( api_router, prefix="/api/v1" )

# Root Endpoints 
@app.get( "/", tags=["root"], summary="Root endpoint")
def root():
    return {
        "message": "AI-Driven Project Management API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }

@app.get( "/health", tags=["health"], summary="Health check")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }