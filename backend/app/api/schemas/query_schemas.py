"""
Query-related Pydantic Models
Request/response models for query generation endpoints
"""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request schema for generating SQL from natural language"""
    schema_id: UUID = Field(..., description="UUID of the schema to query against")
    query: str = Field(
        ...,
        description="Natural language query",
        min_length=1,
        max_length=1000
    )

    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "123e4567-e89b-12d3-a456-426614174000",
                "query": "Show me all users who registered in the last 30 days"
            }
        }


class QueryResponse(BaseModel):
    """Response schema for generated query"""
    id: UUID = Field(..., description="Query UUID")
    natural_language_query: str = Field(..., description="Original natural language query")
    generated_sql: str = Field(..., description="Generated SQL query")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    warnings: List[str] = Field(default=[], description="Any warnings about the generated SQL")
    ai_provider: str = Field(..., description="AI provider used (openai, anthropic)")
    ai_model: str = Field(..., description="Specific AI model used")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "natural_language_query": "Show me all users who registered in the last 30 days",
                "generated_sql": "SELECT * FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' LIMIT 100;",
                "confidence_score": 0.95,
                "warnings": [],
                "ai_provider": "openai",
                "ai_model": "gpt-4o",
                "created_at": "2024-03-14T10:30:00Z"
            }
        }


class QueryHistoryResponse(BaseModel):
    """Response schema for query history"""
    queries: List[QueryResponse] = Field(..., description="List of generated queries")
    total: int = Field(..., description="Total number of queries")

    class Config:
        json_schema_extra = {
            "example": {
                "queries": [],
                "total": 0
            }
        }


class QueryFeedbackRequest(BaseModel):
    """Request schema for query feedback/validation"""
    is_helpful: bool = Field(..., description="Whether the generated SQL was helpful")
    is_correct: bool = Field(..., description="Whether the generated SQL was correct")
    feedback_notes: Optional[str] = Field(
        None,
        description="Optional feedback notes",
        max_length=1000
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_helpful": True,
                "is_correct": True,
                "feedback_notes": "Perfect! Got exactly what I needed."
            }
        }


class QueryFeedbackResponse(BaseModel):
    """Response schema for feedback submission"""
    query_id: UUID = Field(..., description="Query UUID")
    feedback_recorded: bool = Field(..., description="Whether feedback was successfully recorded")
    message: str = Field(..., description="Confirmation message")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "123e4567-e89b-12d3-a456-426614174000",
                "feedback_recorded": True,
                "message": "Thank you for your feedback! This helps improve our SQL generation."
            }
        }


class QueryStatsResponse(BaseModel):
    """Response schema for query statistics"""
    total_queries: int = Field(..., description="Total number of queries generated")
    successful_queries: int = Field(..., description="Number of successful queries")
    failed_queries: int = Field(..., description="Number of failed queries")
    average_confidence: float = Field(..., description="Average confidence score")
    average_execution_time_ms: Optional[float] = Field(None, description="Average execution time in ms")

    class Config:
        json_schema_extra = {
            "example": {
                "total_queries": 150,
                "successful_queries": 142,
                "failed_queries": 8,
                "average_confidence": 0.89,
                "average_execution_time_ms": 245.5
            }
        }


class QueryExampleRequest(BaseModel):
    """Request to create a query example for training"""
    natural_language: str = Field(..., description="Natural language query", max_length=500)
    sql_query: str = Field(..., description="Correct SQL query", max_length=2000)
    explanation: Optional[str] = Field(None, description="Optional explanation", max_length=1000)
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    difficulty: Optional[str] = Field(None, description="Difficulty level (easy, medium, hard)")

    class Config:
        json_schema_extra = {
            "example": {
                "natural_language": "Count all active users",
                "sql_query": "SELECT COUNT(*) FROM users WHERE is_active = true;",
                "explanation": "Simple count with WHERE clause filtering",
                "tags": ["count", "filter", "boolean"],
                "difficulty": "easy"
            }
        }


class QueryExampleResponse(BaseModel):
    """Response schema for query example"""
    id: UUID = Field(..., description="Example UUID")
    natural_language: str = Field(..., description="Natural language query")
    sql_query: str = Field(..., description="SQL query")
    explanation: Optional[str] = Field(None, description="Explanation")
    source: str = Field(..., description="Source of example (manual, auto_generated, user_feedback)")
    quality_score: Optional[int] = Field(None, description="Quality score (1-10)")
    usage_count: int = Field(..., description="Number of times used")
    is_verified: bool = Field(..., description="Whether example is verified")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "natural_language": "Count all active users",
                "sql_query": "SELECT COUNT(*) FROM users WHERE is_active = true;",
                "explanation": "Simple count with WHERE clause filtering",
                "source": "manual",
                "quality_score": 9,
                "usage_count": 15,
                "is_verified": True,
                "created_at": "2024-03-14T10:30:00Z"
            }
        }
