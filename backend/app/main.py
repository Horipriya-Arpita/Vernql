"""
TextSQL API - Main Application Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.core.config import settings
from app.api.v1 import router as api_v1_router
from app.middleware.rate_limiter import RateLimitMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title="TextSQL API",
    description="""
# Text-to-SQL API and Visualization Platform

Convert natural language queries to SQL using AI-powered generation.

## Features

* **Schema Management**: Upload and parse database schemas (PostgreSQL, MySQL)
* **AI Enrichment**: Automatically generate descriptions for tables and columns
* **SQL Generation**: Convert natural language to accurate SQL queries
* **Query History**: Track all generated queries with confidence scores
* **Feedback System**: Improve accuracy through user validation

## Authentication

All endpoints require API key authentication via `X-API-Key` header.

## Getting Started

1. Create an account and get your API key
2. Upload your database schema
3. Start generating SQL queries from natural language

## Support

For issues and feature requests, visit our documentation.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "TextSQL API Support",
        "url": "https://textsql.com/support"
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and status endpoints"
        },
        {
            "name": "Root",
            "description": "Root endpoint with API information"
        },
        {
            "name": "Authentication",
            "description": "API key management and authentication"
        },
        {
            "name": "Schemas",
            "description": "Database schema upload, parsing, and enrichment"
        },
        {
            "name": "Queries",
            "description": "SQL generation from natural language"
        },
        {
            "name": "Integrations",
            "description": "Code snippets and integration examples for various languages"
        }
    ]
)

# Rate Limiting Middleware (inner — must be inside CORS so CORS headers apply to its error responses)
app.add_middleware(RateLimitMiddleware)

# CORS Configuration (outer — must be outermost so all responses get CORS headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()

    # Log request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )

    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=f"{process_time:.3f}s"
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        path=request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns 200 if service is healthy
    """
    return {
        "status": "healthy",
        "service": "textsql-api",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "TextSQL API",
        "version": "1.0.0",
        "description": "Text-to-SQL API and Visualization Platform",
        "docs": "/docs",
        "health": "/health"
    }


# Include API v1 router
app.include_router(
    api_v1_router,
    prefix="/v1"
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
