"""
API v1 Router
Aggregates all v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1 import auth, schemas, queries, integrations, visualizations, sessions

# Create main router
router = APIRouter()

# Include routers
router.include_router(auth.router)
router.include_router(schemas.router)
router.include_router(queries.router)
router.include_router(integrations.router)
router.include_router(visualizations.router)
router.include_router(sessions.router)

# Placeholder endpoints
@router.get("/ping")
async def ping():
    """Test endpoint - no authentication required"""
    return {"message": "pong", "version": "1.0.0"}
