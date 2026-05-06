"""
JWT Token Management
Handles JWT token creation, validation, and refresh
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token

    Example:
        token = create_access_token({"sub": str(user.id), "email": user.email})
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    # Encode token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    logger.info("Access token created", user_id=data.get("sub"))

    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token (longer expiration)

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT refresh token

    Example:
        token = create_refresh_token({"sub": str(user.id)})
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    # Encode token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    logger.info("Refresh token created", user_id=data.get("sub"))

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload if valid, None otherwise

    Validation checks:
        - Token signature is valid
        - Token has not expired
        - Token type matches expected type
    """
    try:
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(
                "Invalid token type",
                expected=token_type,
                actual=payload.get("type")
            )
            return None

        logger.info("Token verified successfully", user_id=payload.get("sub"))

        return payload

    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification (for debugging)

    Args:
        token: JWT token string to decode

    Returns:
        Optional[Dict[str, Any]]: Decoded token payload (unverified)

    Warning:
        This does not verify the token signature! Use verify_token() for production.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False}
        )
        return payload
    except JWTError as e:
        logger.warning("Token decode failed", error=str(e))
        return None