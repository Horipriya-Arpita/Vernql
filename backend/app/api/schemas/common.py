"""
Common Pydantic Schemas
Shared schemas used across multiple endpoints
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Resource not found",
                "detail": "Schema with ID abc123 does not exist",
                "code": "SCHEMA_NOT_FOUND"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional additional data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 50
            }
        }


class PaginatedResponse(BaseModel):
    """Base class for paginated responses"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        """Create paginated response"""
        import math
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size > 0 else 0
        }
