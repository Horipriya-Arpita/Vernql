"""
FastAPI dependencies for authentication and authorization
"""
from typing import Annotated
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import structlog

from app.db.database import get_db
from app.core.security import verify_api_key
from app.models import Company, APIKey

logger = structlog.get_logger()

# API Key header authentication scheme
api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="Your TextSQL API key",
    auto_error=False  # Don't auto-raise error, we'll handle it
)


async def get_current_company(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> tuple[Company, APIKey]:
    """
    Dependency to get the current authenticated company from API key

    Args:
        api_key: API key from X-API-Key header
        db: Database session

    Returns:
        tuple[Company, APIKey]: Authenticated company and API key objects

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide your API key in the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify the API key
    result = verify_api_key(db, api_key)

    if not result:
        logger.warning("Invalid API key", key_prefix=api_key[:10])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    company, api_key_obj = result

    logger.info(
        "Request authenticated",
        company_id=str(company.id),
        company_name=company.name
    )

    return company, api_key_obj


async def get_current_active_company(
    auth: tuple[Company, APIKey] = Depends(get_current_company)
) -> Company:
    """
    Dependency to get only the current company (syntactic sugar)

    Args:
        auth: Authenticated company and API key from get_current_company

    Returns:
        Company: The authenticated company
    """
    company, _ = auth
    return company


# Type aliases for cleaner endpoint signatures
CurrentCompany = Annotated[Company, Depends(get_current_active_company)]
CurrentAuth = Annotated[tuple[Company, APIKey], Depends(get_current_company)]
