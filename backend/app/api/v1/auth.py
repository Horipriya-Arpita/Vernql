"""
Authentication and API Key Management Endpoints
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
import structlog

from app.db.database import get_db
from app.core.dependencies import CurrentCompany, CurrentCompanyEither, CurrentUser
from app.core.security import create_api_key, hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token, verify_token
from app.models import APIKey, User, Company

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# User Registration & Login Schemas
# ============================================================================

class UserRegister(BaseModel):
    """Request schema for user registration"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    company_name: str = Field(..., min_length=2, max_length=255, description="Company/Organization name")


class UserLogin(BaseModel):
    """Request schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Response schema for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token expiration time in seconds")


class UserResponse(BaseModel):
    """Response schema for user information"""
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_email_verified: bool
    is_admin: bool
    company_id: UUID
    company_name: str
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Combined response for registration/login"""
    user: UserResponse
    tokens: TokenResponse


class UserUpdate(BaseModel):
    """Request schema for updating user profile"""
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")


class PasswordChange(BaseModel):
    """Request schema for changing password"""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)")


# ============================================================================
# User Registration & Login Endpoints
# ============================================================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and company"
)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user and create their company account

    This endpoint creates:
    1. A new company
    2. A new user account (as company admin)
    3. JWT tokens for immediate authentication

    ## Parameters
    - **email**: User's email address (must be unique)
    - **password**: Strong password (minimum 8 characters)
    - **full_name**: User's full name (optional)
    - **company_name**: Name of the company/organization

    ## Response
    Returns user information and authentication tokens

    ## Errors
    - **400**: Email already registered
    - **422**: Validation error (invalid email, weak password, etc.)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning("Registration attempt with existing email", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )

    # Create company
    company = Company(
        name=user_data.company_name,
        is_active=True
    )
    db.add(company)
    db.flush()  # Get company ID without committing

    # Hash password
    hashed_pwd = hash_password(user_data.password)

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        company_id=company.id,
        is_active=True,
        is_admin=True,  # First user is admin
        is_email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(company)

    logger.info(
        "User registered successfully",
        user_id=str(user.id),
        email=user.email,
        company_id=str(company.id)
    )

    # Generate tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Prepare response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        is_admin=user.is_admin,
        company_id=company.id,
        company_name=company.name,
        created_at=user.created_at,
        last_login_at=user.last_login_at
    )

    tokens = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600  # 1 hour
    )

    return AuthResponse(user=user_response, tokens=tokens)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password"
)
async def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with email and password

    ## Parameters
    - **email**: User's email address
    - **password**: User's password

    ## Response
    Returns user information and authentication tokens

    ## Errors
    - **401**: Invalid credentials or inactive account
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning("Failed login attempt", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning("Login attempt for inactive user", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get company
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company or not company.is_active:
        logger.warning("Login attempt for inactive company", company_id=str(user.company_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Company account is inactive. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    logger.info("User logged in successfully", user_id=str(user.id), email=user.email)

    # Generate tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Prepare response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        is_admin=user.is_admin,
        company_id=company.id,
        company_name=company.name,
        created_at=user.created_at,
        last_login_at=user.last_login_at
    )

    tokens = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600  # 1 hour
    )

    return AuthResponse(user=user_response, tokens=tokens)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information"
)
async def get_current_user_info(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Get information about the currently authenticated user (JWT-based)

    Requires a valid JWT token in the Authorization header.

    ## Response
    Returns user and company information
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        is_admin=current_user.is_admin,
        company_id=current_user.company_id,
        company_name=company.name if company else "Unknown",
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile"
)
async def update_current_user(
    update_data: UserUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile information

    ## Parameters
    - **full_name**: Update user's full name
    - **email**: Update email address (must be unique)

    ## Response
    Returns updated user information
    """
    update_dict = update_data.model_dump(exclude_unset=True)

    # Check if email is being changed and if it's already taken
    if 'email' in update_dict and update_dict['email'] != current_user.email:
        existing_user = db.query(User).filter(
            User.email == update_dict['email'],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already in use"
            )

    # Update user fields
    for field, value in update_dict.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    logger.info("User profile updated", user_id=str(current_user.id))

    # Get company info
    company = db.query(Company).filter(Company.id == current_user.company_id).first()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        is_admin=current_user.is_admin,
        company_id=current_user.company_id,
        company_name=company.name if company else "Unknown",
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user password"
)
async def change_password(
    password_data: PasswordChange,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Change the current user's password

    ## Parameters
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)

    ## Response
    Returns success message
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        logger.warning("Failed password change attempt", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash and update new password
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()

    logger.info("Password changed successfully", user_id=str(current_user.id))

    return {
        "message": "Password changed successfully",
        "success": True
    }


# ============================================================================
# API Key Management Schemas & Endpoints (Existing)
# ============================================================================

# Pydantic schemas
class APIKeyCreate(BaseModel):
    """Request schema for creating a new API key"""
    name: Optional[str] = Field(None, description="Friendly name for the API key", max_length=100)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000, description="Custom rate limit per minute")
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000, description="Custom rate limit per hour")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (null = never expires)")


_EXPIRY_WARNING_DAYS = 7  # show warning badge when this many days remain


class APIKeyResponse(BaseModel):
    """Response schema for API key (without the actual key)"""
    id: UUID
    name: Optional[str]
    is_active: bool
    rate_limit_per_minute: Optional[int]
    rate_limit_per_hour: Optional[int]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    # Computed expiry helpers — null when the key has no expiry date
    days_until_expiry: Optional[int] = None
    is_expiring_soon:  bool          = False

    class Config:
        from_attributes = True

    @classmethod
    def from_api_key(cls, key: "APIKey") -> "APIKeyResponse":
        """Build response with computed expiry warning fields."""
        days: Optional[int] = None
        expiring_soon = False
        if key.expires_at:
            from datetime import timezone
            delta = key.expires_at - datetime.now(timezone.utc)
            days = max(0, delta.days)
            expiring_soon = days <= _EXPIRY_WARNING_DAYS
        return cls(
            id=key.id,
            name=key.name,
            is_active=key.is_active,
            rate_limit_per_minute=key.rate_limit_per_minute,
            rate_limit_per_hour=key.rate_limit_per_hour,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            days_until_expiry=days,
            is_expiring_soon=expiring_soon,
        )


class APIKeyCreateResponse(BaseModel):
    """Response schema when creating a new API key (includes the raw key)"""
    api_key: str = Field(..., description="The raw API key - save this! It won't be shown again")
    key_info: APIKeyResponse


class APIKeyListResponse(BaseModel):
    """Response schema for listing API keys"""
    keys: List[APIKeyResponse]
    total: int


@router.post(
    "/keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key"
)
async def create_new_api_key(
    key_data: APIKeyCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the authenticated company

    **Important:** The raw API key is only shown once in the response.
    Store it securely - you won't be able to retrieve it later!

    ## Parameters
    - **name**: Optional friendly name for the key
    - **rate_limit_per_minute**: Override default rate limit per minute
    - **rate_limit_per_hour**: Override default rate limit per hour
    - **expires_at**: Optional expiration datetime (null = never expires)

    ## Response
    Returns the new API key and its metadata
    """
    # Create the API key
    raw_key, api_key_obj = create_api_key(
        db=db,
        company_id=str(current_user.company_id),
        name=key_data.name,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        expires_at=key_data.expires_at
    )

    return APIKeyCreateResponse(
        api_key=raw_key,
        key_info=APIKeyResponse.from_api_key(api_key_obj)
    )


@router.get(
    "/keys",
    response_model=APIKeyListResponse,
    summary="List all API keys"
)
async def list_api_keys(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """
    List all API keys for the authenticated company

    ## Parameters
    - **include_inactive**: Include revoked/inactive keys in the response

    ## Response
    Returns a list of API keys (without the actual key values)
    """
    query = db.query(APIKey).filter(APIKey.company_id == current_user.company_id)

    if not include_inactive:
        query = query.filter(APIKey.is_active == True)

    keys = query.order_by(APIKey.created_at.desc()).all()

    return APIKeyListResponse(
        keys=[APIKeyResponse.from_api_key(key) for key in keys],
        total=len(keys)
    )


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key"
)
async def revoke_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Revoke (deactivate) an API key

    This marks the key as inactive - it won't be deleted from the database
    but will no longer work for authentication.

    ## Parameters
    - **key_id**: UUID of the API key to revoke

    ## Response
    Returns 204 No Content on success
    """
    # Find the API key
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.company_id == current_user.company_id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Revoke the key
    api_key.is_active = False
    db.commit()

    return None


class UpdateAPIKeyRequest(BaseModel):
    """Request schema for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)


@router.patch(
    "/keys/{key_id}",
    response_model=APIKeyResponse,
    summary="Update API key settings"
)
async def update_api_key(
    key_id: UUID,
    updates: UpdateAPIKeyRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update an API key's name or rate limits.

    Note: You cannot change the actual key value. To get a new key,
    revoke the old one and create a new one.
    """
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.company_id == current_user.company_id
    ).first()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    if updates.name is not None:
        key.name = updates.name
    if updates.rate_limit_per_minute is not None:
        key.rate_limit_per_minute = updates.rate_limit_per_minute
    if updates.rate_limit_per_hour is not None:
        key.rate_limit_per_hour = updates.rate_limit_per_hour

    db.commit()
    db.refresh(key)

    return APIKeyResponse.from_api_key(key)


@router.post(
    "/keys/{key_id}/activate",
    response_model=APIKeyResponse,
    summary="Reactivate a revoked API key"
)
async def activate_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Reactivate a previously revoked API key.

    Only works if the key has not expired. If it has expired,
    create a new one instead.
    """
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.company_id == current_user.company_id
    ).first()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    if key.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reactivate an expired key. Create a new one instead."
        )

    key.is_active = True
    db.commit()
    db.refresh(key)

    return APIKeyResponse.from_api_key(key)


@router.get(
    "/company/me",
    response_model=dict,
    summary="Get current company info"
)
async def get_current_company_info(
    company: CurrentCompanyEither
):
    """
    Get information about the currently authenticated company

    Accepts either JWT token (Authorization: Bearer) or API Key (X-API-Key) authentication.
    Useful for testing authentication and verifying company access.

    ## Response
    Returns company information
    """
    return {
        "company_id": str(company.id),
        "company_name": company.name,
        "is_active": company.is_active,
        "created_at": company.created_at,
        "authenticated": True
    }
