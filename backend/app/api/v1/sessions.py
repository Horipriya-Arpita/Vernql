"""
Session Endpoints
Manages conversational sessions for multi-turn NL2SQL queries.
SSE stream endpoint is also defined here.
"""
import asyncio
import json
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

from app.core.redis_client import get_redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.core.config import settings
from app.services.visualization_service import VisualizationService
from app.core.dependencies import CurrentCompanyEither
from app.services.session_service import SessionService, SessionTurn

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SessionCreateRequest(BaseModel):
    schema_id: Optional[UUID] = Field(None, description="Default schema UUID for this session")


class SessionResponse(BaseModel):
    session_id: UUID
    schema_id: Optional[UUID]
    title: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class SessionTurnResponse(BaseModel):
    turn_number: int
    query_id: UUID
    natural_language_query: str
    generated_sql: str
    result_id: Optional[UUID]
    chart_type: Optional[str]
    ai_insight: Optional[str]
    visualization_data: Optional[Any]
    created_at: datetime


class SessionHistoryResponse(BaseModel):
    session_id: UUID
    turns: List[SessionTurnResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session_to_response(session) -> SessionResponse:
    return SessionResponse(
        session_id=session.id,
        schema_id=session.schema_id,
        title=session.title,
        is_active=session.is_active,
        created_at=session.created_at
    )


def _turn_to_response(turn: SessionTurn) -> SessionTurnResponse:
    return SessionTurnResponse(
        turn_number=turn.turn_number,
        query_id=turn.query_id,
        natural_language_query=turn.natural_language_query,
        generated_sql=turn.generated_sql,
        result_id=turn.result_id,
        chart_type=turn.chart_type,
        ai_insight=turn.ai_insight,
        visualization_data=turn.visualization_data,
        created_at=turn.created_at
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session"
)
async def create_session(
    body: SessionCreateRequest,
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db)
):
    """
    Start a new conversational session.

    A session groups multiple NL→SQL queries so the user can ask follow-up
    questions without re-specifying context each time.

    ## Flow
    1. POST /sessions → get session_id
    2. POST /queries with session_id → get SQL (turn 1, 2, 3 …)
    3. POST /visualizations/display with session_id → push result to SSE
    4. Widget connected to GET /sessions/{id}/stream auto-refreshes
    """
    svc = SessionService(db)
    session = svc.create_session(
        company_id=company.id,
        schema_id=body.schema_id
    )
    return _session_to_response(session)


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List sessions for the authenticated company"
)
async def list_sessions(
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Return all sessions for the company, newest first."""
    limit = min(limit, 100)
    svc = SessionService(db)
    sessions = svc.list_sessions(company_id=company.id, limit=limit, offset=offset)
    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions],
        total=len(sessions)
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get a session by ID"
)
async def get_session(
    session_id: UUID,
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db)
):
    """Fetch a single session, scoped to the authenticated company."""
    svc = SessionService(db)
    session = svc.get_session(session_id=session_id, company_id=company.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _session_to_response(session)


@router.get(
    "/{session_id}/history",
    response_model=SessionHistoryResponse,
    summary="Get all turns in a session"
)
async def get_session_history(
    session_id: UUID,
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db)
):
    """
    Return all query/result pairs in this session in chronological order.

    Each turn contains the natural language question, generated SQL,
    and the visualization data (if results have been submitted).
    """
    svc = SessionService(db)
    try:
        turns = svc.get_history(session_id=session_id, company_id=company.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return SessionHistoryResponse(
        session_id=session_id,
        turns=[_turn_to_response(t) for t in turns]
    )


@router.get(
    "/{session_id}/latest",
    summary="Get the most recent visualization in a session"
)
async def get_latest_result(
    session_id: UUID,
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db)
):
    """
    Returns the most recent QueryResult for this session.
    Useful for the embed iframe to know what chart to show on load.
    """
    svc = SessionService(db)
    try:
        result = svc.get_latest_result(session_id=session_id, company_id=company.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not result:
        return {"session_id": session_id, "result": None}

    viz_data = VisualizationService.prepare_visualization_data(
        results=result.results_data,
        chart_type=result.chart_type
    )

    return {
        "session_id": session_id,
        "result_id": result.id,
        "chart_type": result.chart_type,
        "ai_insight": result.ai_insight,
        "visualization_data": viz_data,
        "created_at": result.created_at
    }


@router.get(
    "/{session_id}/stream",
    summary="SSE stream — receive live updates as new results are published"
)
async def stream_session(
    session_id: UUID,
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db)
):
    """
    Server-Sent Events stream for a session.

    Keeps the connection open and pushes one `new_result` event each time a
    result is stored for this session via POST /visualizations/display.

    The client (e.g., an embedded widget) connects once and the chart
    re-renders automatically without polling.

    SSE auto-reconnects on disconnect (built into the spec).
    """
    # Verify session ownership before opening long-lived connection
    svc = SessionService(db)
    session = svc.get_session(session_id=session_id, company_id=company.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    async def event_generator():
        # Use the shared pool — create a dedicated pubsub object from it.
        # We close only the pubsub on teardown, NOT the underlying pool client,
        # so other concurrent requests keep their connections alive.
        pubsub = get_redis().pubsub()
        channel = f"session:{session_id}"

        await pubsub.subscribe(channel)
        try:
            # Send a heartbeat comment every 15 s to keep the connection alive
            # through proxies/load balancers.
            while True:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=15.0)
                if message and message["type"] == "message":
                    data = message["data"]
                    yield f"event: new_result\ndata: {data}\n\n"
                else:
                    # Heartbeat (SSE comment — ignored by clients)
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable Nginx buffering
        }
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session"
)
async def delete_session(
    session_id: UUID,
    company: CurrentCompanyEither,
    db: DBSession = Depends(get_db)
):
    """
    Delete a session and all its associated queries and results (via DB cascade).
    """
    svc = SessionService(db)
    deleted = svc.delete_session(session_id=session_id, company_id=company.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return None