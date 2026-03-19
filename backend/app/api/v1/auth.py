"""
Authentication and API Key Management Endpoints
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import CurrentCompany
from app.core.security import create_api_key
from app.models import APIKey

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic schemas
class APIKeyCreate(BaseModel):
    """Request schema for creating a new API key"""
    name: Optional[str] = Field(None, description="Friendly name for the API key", max_length=100)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000, description="Custom rate limit per minute")
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000, description="Custom rate limit per hour")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (null = never expires)")


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

    class Config:
        from_attributes = True


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
    company: CurrentCompany,
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
        company_id=str(company.id),
        name=key_data.name,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        expires_at=key_data.expires_at
    )

    return APIKeyCreateResponse(
        api_key=raw_key,
        key_info=APIKeyResponse.from_orm(api_key_obj)
    )


@router.get(
    "/keys",
    response_model=APIKeyListResponse,
    summary="List all API keys"
)
async def list_api_keys(
    company: CurrentCompany,
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
    query = db.query(APIKey).filter(APIKey.company_id == company.id)

    if not include_inactive:
        query = query.filter(APIKey.is_active == True)

    keys = query.order_by(APIKey.created_at.desc()).all()

    return APIKeyListResponse(
        keys=[APIKeyResponse.from_orm(key) for key in keys],
        total=len(keys)
    )


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key"
)
async def revoke_api_key(
    key_id: UUID,
    company: CurrentCompany,
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
        APIKey.company_id == company.id
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


@router.get(
    "/me",
    response_model=dict,
    summary="Get current authentication info"
)
async def get_current_auth_info(
    company: CurrentCompany
):
    """
    Get information about the currently authenticated company

    Useful for testing authentication and verifying API keys.

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
