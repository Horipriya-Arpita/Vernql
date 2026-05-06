"""
Visualization & Results Display Endpoints
Handles storing query results and serving visualizations
"""
import json
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import redis.asyncio as aioredis

from app.db.database import get_db
from app.core.config import settings
from app.core.dependencies import CurrentCompany, CurrentCompanyEither
from app.services.results_service import ResultsService
from app.services.visualization_service import VisualizationService
from app.core.ai_client import get_ai_client

router = APIRouter(prefix="/visualizations", tags=["Visualizations"])


# Pydantic schemas
class DisplayRequest(BaseModel):
    """Request to store and visualize query results"""
    query_id: UUID = Field(..., description="UUID of the query that generated these results")
    results: List[Dict[str, Any]] = Field(
        ...,
        description="Array of result rows from query execution",
        examples=[[
            {"product": "Widget A", "sales": 1500},
            {"product": "Widget B", "sales": 2300}
        ]]
    )
    generate_insight: bool = Field(
        default=True,
        description="Whether to generate AI insight about the results"
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Optional session UUID — stores result in session and pushes SSE event"
    )


class VisualizationDataResponse(BaseModel):
    """Prepared visualization data for frontend"""
    type: str = Field(..., description="Chart type: metric, bar, line, pie, table")
    data: Any = Field(default=None, description="Formatted data for the chart type")
    columns: Optional[List[str]] = Field(default=None, description="Column names for table type")
    value: Optional[Any] = Field(default=None, description="Metric value")
    label: Optional[str] = Field(default=None, description="Metric label")


class VisualizationResponse(BaseModel):
    """Response with visualization details"""
    id: UUID
    query_id: UUID
    chart_type: str
    row_count: int
    column_count: int
    ai_insight: Optional[str]
    visualization_data: VisualizationDataResponse
    is_public: bool
    created_at: datetime
    visualization_url: str

    class Config:
        from_attributes = True


class ResultListItem(BaseModel):
    """List item for query results"""
    id: UUID
    query_id: UUID
    chart_type: str
    row_count: int
    ai_insight: Optional[str]
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResultListResponse(BaseModel):
    """Response for list of results"""
    results: List[ResultListItem]
    total: int


class SharingUpdateRequest(BaseModel):
    """Request to update sharing settings"""
    is_public: bool = Field(..., description="Whether to make this visualization publicly shareable")


@router.post(
    "/display",
    response_model=VisualizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store query results and generate visualization"
)
async def display_results(
    request: DisplayRequest,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Store query results and auto-generate visualization

    This endpoint completes the TextSQL flow:
    1. Client calls /queries to get SQL
    2. Client runs SQL on their own database
    3. Client POSTs results to this endpoint
    4. API returns visualization URL and auto-detected chart type

    **Chart Type Auto-Detection:**
    - Single metric → Metric card
    - Categories + values → Pie or Bar chart
    - Time series → Line chart
    - Everything else → Table

    **AI Insights:**
    - Optionally generates a one-line summary of the data
    - Example: "Sales increased 23% compared to last month"
    """
    try:
        # Get AI client if insights requested
        ai_client = None
        if request.generate_insight:
            ai_client = get_ai_client()

        # Store results and generate visualization
        results_service = ResultsService(db)
        query_result = await results_service.store_results(
            query_id=request.query_id,
            company_id=company.id,
            results_data=request.results,
            ai_client=ai_client,
            session_id=request.session_id
        )

        # Prepare visualization data for frontend
        viz_data = VisualizationService.prepare_visualization_data(
            results=query_result.results_data,
            chart_type=query_result.chart_type
        )

        # If this result belongs to a session, publish to Redis so SSE clients update
        if request.session_id is not None:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            payload = json.dumps({
                "result_id": str(query_result.id),
                "chart_type": query_result.chart_type,
                "ai_insight": query_result.ai_insight,
                "visualization_data": viz_data
            })
            await redis_client.publish(f"session:{request.session_id}", payload)
            await redis_client.aclose()

        # Build response
        return VisualizationResponse(
            id=query_result.id,
            query_id=query_result.query_id,
            chart_type=query_result.chart_type,
            row_count=query_result.row_count,
            column_count=query_result.column_count,
            ai_insight=query_result.ai_insight,
            visualization_data=viz_data,
            is_public=query_result.is_public,
            created_at=query_result.created_at,
            visualization_url=f"/visualizations/{query_result.id}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store results: {str(e)}"
        )


@router.get(
    "/{result_id}",
    response_model=VisualizationResponse,
    summary="Get visualization by ID"
)
async def get_visualization(
    result_id: UUID,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Retrieve a stored visualization by ID

    Requires company authentication - only returns visualizations
    belonging to the authenticated company.
    """
    results_service = ResultsService(db)
    query_result = results_service.get_result(
        result_id=result_id,
        company_id=company.id
    )

    if not query_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visualization not found or access denied"
        )

    # Prepare visualization data
    viz_data = VisualizationService.prepare_visualization_data(
        results=query_result.results_data,
        chart_type=query_result.chart_type
    )

    return VisualizationResponse(
        id=query_result.id,
        query_id=query_result.query_id,
        chart_type=query_result.chart_type,
        row_count=query_result.row_count,
        column_count=query_result.column_count,
        ai_insight=query_result.ai_insight,
        visualization_data=viz_data,
        is_public=query_result.is_public,
        created_at=query_result.created_at,
        visualization_url=f"/visualizations/{query_result.id}"
    )


@router.get(
    "/public/{result_id}",
    response_model=VisualizationResponse,
    summary="Get public visualization (no auth required)"
)
async def get_public_visualization(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a public visualization by ID

    No authentication required - only returns publicly shared visualizations.
    Use this endpoint for embedding visualizations in external websites.
    """
    results_service = ResultsService(db)
    query_result = results_service.get_result(
        result_id=result_id,
        company_id=None  # None = public access only
    )

    if not query_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public visualization not found"
        )

    # Prepare visualization data
    viz_data = VisualizationService.prepare_visualization_data(
        results=query_result.results_data,
        chart_type=query_result.chart_type
    )

    return VisualizationResponse(
        id=query_result.id,
        query_id=query_result.query_id,
        chart_type=query_result.chart_type,
        row_count=query_result.row_count,
        column_count=query_result.column_count,
        ai_insight=query_result.ai_insight,
        visualization_data=viz_data,
        is_public=query_result.is_public,
        created_at=query_result.created_at,
        visualization_url=f"/visualizations/{query_result.id}"
    )


@router.get(
    "",
    response_model=ResultListResponse,
    summary="List all visualizations for company"
)
async def list_visualizations(
    company: CurrentCompanyEither,
    query_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all visualizations for the authenticated company

    Optionally filter by query_id to see all visualizations
    from a specific query.
    """
    results_service = ResultsService(db)
    results = results_service.list_results(
        company_id=company.id,
        query_id=query_id,
        limit=limit,
        offset=offset
    )

    return ResultListResponse(
        results=[
            ResultListItem(
                id=r.id,
                query_id=r.query_id,
                chart_type=r.chart_type,
                row_count=r.row_count,
                ai_insight=r.ai_insight,
                is_public=r.is_public,
                created_at=r.created_at
            )
            for r in results
        ],
        total=len(results)
    )


@router.patch(
    "/{result_id}/sharing",
    response_model=VisualizationResponse,
    summary="Update sharing settings"
)
async def update_sharing(
    result_id: UUID,
    request: SharingUpdateRequest,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Make a visualization public or private

    Public visualizations can be accessed via /visualizations/public/{id}
    without authentication, making them embeddable in external websites.
    """
    results_service = ResultsService(db)
    query_result = results_service.make_public(
        result_id=result_id,
        company_id=company.id,
        is_public=request.is_public
    )

    if not query_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visualization not found or access denied"
        )

    # Prepare visualization data
    viz_data = VisualizationService.prepare_visualization_data(
        results=query_result.results_data,
        chart_type=query_result.chart_type
    )

    return VisualizationResponse(
        id=query_result.id,
        query_id=query_result.query_id,
        chart_type=query_result.chart_type,
        row_count=query_result.row_count,
        column_count=query_result.column_count,
        ai_insight=query_result.ai_insight,
        visualization_data=viz_data,
        is_public=query_result.is_public,
        created_at=query_result.created_at,
        visualization_url=f"/visualizations/{query_result.id}"
    )


@router.delete(
    "/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a visualization"
)
async def delete_visualization(
    result_id: UUID,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Delete a visualization

    This removes the stored results and visualization data.
    The original query in query history remains untouched.
    """
    results_service = ResultsService(db)
    success = results_service.delete_result(
        result_id=result_id,
        company_id=company.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visualization not found or access denied"
        )

    return None