"""
Security utilities for API key generation and validation, and password hashing
"""
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import structlog

from app.core.config import settings
from app.models import APIKey, Company

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> str:
    """
    Generate a new API key with the configured prefix

    Returns:
        str: A new API key in format: {prefix}_{random_token}

    Example:
        textsql_abc123def456...
    """
    random_token = secrets.token_urlsafe(settings.API_KEY_LENGTH)
    api_key = f"{settings.API_KEY_PREFIX}{random_token}"
    return api_key


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256

    Args:
        api_key: The raw API key to hash

    Returns:
        str: The hexadecimal hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(db: Session, api_key: str) -> Optional[tuple[Company, APIKey]]:
    """
    Verify an API key and return the associated company and key object

    Args:
        db: Database session
        api_key: The raw API key to verify

    Returns:
        Optional[tuple[Company, APIKey]]: Company and APIKey objects if valid, None otherwise

    Validation checks:
        - Key exists in database
        - Key is active
        - Key has not expired
        - Associated company is active
    """
    # Hash the provided key
    key_hash = hash_api_key(api_key)

    # Query for the API key with its company
    api_key_obj = (
        db.query(APIKey)
        .filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
        .first()
    )

    if not api_key_obj:
        logger.warning("API key not found or inactive", key_hash=key_hash[:10])
        return None

    # Check if key has expired
    if api_key_obj.is_expired():
        logger.warning("API key expired", api_key_id=str(api_key_obj.id))
        return None

    # Get the associated company
    company = (
        db.query(Company)
        .filter(
            Company.id == api_key_obj.company_id,
            Company.is_active == True
        )
        .first()
    )

    if not company:
        logger.warning(
            "Company not found or inactive",
            company_id=str(api_key_obj.company_id)
        )
        return None

    # Update last_used_at timestamp
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "API key verified successfully",
        company_id=str(company.id),
        api_key_id=str(api_key_obj.id)
    )

    return company, api_key_obj


def create_api_key(
    db: Session,
    company_id: str,
    name: Optional[str] = None,
    rate_limit_per_minute: Optional[int] = None,
    rate_limit_per_hour: Optional[int] = None,
    expires_at: Optional[datetime] = None
) -> tuple[str, APIKey]:
    """
    Create a new API key for a company

    Args:
        db: Database session
        company_id: UUID of the company
        name: Optional friendly name for the key
        rate_limit_per_minute: Optional custom rate limit per minute
        rate_limit_per_hour: Optional custom rate limit per hour
        expires_at: Optional expiration datetime

    Returns:
        tuple[str, APIKey]: The raw API key and the APIKey object

    Note:
        The raw API key is only returned once and cannot be retrieved later.
        Store it securely!
    """
    # Generate new API key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    # Create API key object
    api_key_obj = APIKey(
        company_id=company_id,
        key_hash=key_hash,
        name=name,
        is_active=True,
        rate_limit_per_minute=rate_limit_per_minute,
        rate_limit_per_hour=rate_limit_per_hour,
        expires_at=expires_at
    )

    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    logger.info(
        "API key created",
        company_id=company_id,
        api_key_id=str(api_key_obj.id),
        name=name
    )

    return raw_key, api_key_obj


# ============================================================================
# Password Utilities
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password

    Example:
        hashed = hash_password("my_secure_password")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        is_valid = verify_password("user_input", stored_hash)
    """
    return pwd_context.verify(plain_password, hashed_password)
