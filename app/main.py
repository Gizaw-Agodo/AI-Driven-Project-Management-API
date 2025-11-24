from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.middleware.error_handlers import register_exception_handlers
from app.api.v1.api import api_router


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎓 STEP 4: Register Exception Handlers
register_exception_handlers(app)

# 🎓 STEP 5: Include API Routes
app.include_router( api_router, prefix="/api/v1" )


@app.get(
    "/",
    tags=["root"],
    summary="Root endpoint"
)
def root():
    return {
        "message": "AI-Driven Project Management API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Health check"
)

def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }