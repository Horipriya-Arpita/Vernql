"""
FastAPI dependencies for authentication and authorization
"""
from typing import Annotated
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog

from app.db.database import get_db
from app.core.security import verify_api_key
from app.core.jwt import verify_token
from app.models import Company, APIKey, User

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


# JWT Bearer authentication scheme
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        logger.warning("Missing JWT token in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token. Provide a valid JWT token in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the token
    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if not payload:
        logger.warning("Invalid JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        logger.warning("User not found or inactive", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "Request authenticated with JWT",
        user_id=str(user.id),
        email=user.email
    )

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active (syntactic sugar)

    Args:
        user: Authenticated user from get_current_user

    Returns:
        User: The authenticated active user
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return user


async def get_company_from_either_auth(
    api_key: str = Security(api_key_header),
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
    db: Session = Depends(get_db)
) -> Company:
    """
    Unified authentication dependency that accepts EITHER:
    - JWT Bearer token (Authorization: Bearer <token>)
    - API Key (X-API-Key: <key>)

    This allows both registered users (JWT) and API key users to access endpoints.

    Args:
        api_key: Optional API key from X-API-Key header
        credentials: Optional JWT Bearer token from Authorization header
        db: Database session

    Returns:
        Company: Authenticated company object

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Try JWT authentication first
    if credentials:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")

        if payload:
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
                if user and user.company:
                    # Update last login time
                    user.last_login_at = datetime.now(timezone.utc)
                    db.commit()

                    logger.info(
                        "Request authenticated with JWT",
                        user_id=str(user.id),
                        email=user.email,
                        company_id=str(user.company_id)
                    )
                    return user.company

    # Try API key authentication as fallback
    if api_key:
        result = verify_api_key(db, api_key)
        if result:
            company, api_key_obj = result
            logger.info(
                "Request authenticated with API key",
                company_id=str(company.id),
                company_name=company.name
            )
            return company

    # No valid authentication provided
    logger.warning("Missing or invalid authentication credentials")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either a valid JWT token (Authorization: Bearer <token>) or API key (X-API-Key: <key>).",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Type aliases for cleaner endpoint signatures
CurrentCompany = Annotated[Company, Depends(get_current_active_company)]
CurrentAuth = Annotated[tuple[Company, APIKey], Depends(get_current_company)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
# Unified authentication - accepts JWT or API key
CurrentCompanyEither = Annotated[Company, Depends(get_company_from_either_auth)]
