"""
Session Service
Manages conversational sessions — grouping multiple queries under one session.
All methods enforce company_id scoping so a company can never touch another's session.
"""
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.models.session import Session
from app.models.query import Query
from app.models.query_result import QueryResult
from app.services.visualization_service import VisualizationService

logger = structlog.get_logger()


@dataclass
class SessionTurn:
    """
    One turn in a conversation — query + its result joined together.
    This is what the frontend chat UI renders per message pair.
    """
    turn_number: int
    query_id: UUID
    natural_language_query: str
    generated_sql: str
    result_id: Optional[UUID]
    chart_type: Optional[str]
    ai_insight: Optional[str]
    visualization_data: Optional[dict]
    created_at: datetime


class SessionService:
    """
    Service for creating and managing conversational sessions.
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_session(
        self,
        company_id: UUID,
        schema_id: Optional[UUID] = None
    ) -> Session:
        """
        Create a new session for a company.

        Args:
            company_id: The owning company's UUID.
            schema_id:  Optional default schema for the session.

        Returns:
            The newly created Session row.
        """
        try:
            session = Session(
                company_id=company_id,
                schema_id=schema_id,
                is_active=True
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            logger.info("Session created", session_id=str(session.id), company_id=str(company_id))
            return session

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create session", error=str(e))
            raise

    def get_session(
        self,
        session_id: UUID,
        company_id: UUID
    ) -> Optional[Session]:
        """
        Fetch a session, validating it belongs to the given company.

        Returns None if not found or ownership mismatch.
        """
        return self.db.query(Session).filter(
            Session.id == session_id,
            Session.company_id == company_id
        ).first()

    def get_or_create(
        self,
        company_id: UUID,
        schema_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Session:
        """
        If session_id is provided, validate it and return the existing session.
        If session_id is None, create and return a new session.

        Raises:
            ValueError: If session_id given but not found / wrong company.
        """
        if session_id is not None:
            session = self.get_session(session_id, company_id)
            if not session:
                raise ValueError(f"Session {session_id} not found or access denied")
            return session

        return self.create_session(company_id=company_id, schema_id=schema_id)

    def get_history(
        self,
        session_id: UUID,
        company_id: UUID
    ) -> List[SessionTurn]:
        """
        Return all turns in a session in chronological order.

        Each turn joins the Query row with its most recent QueryResult.

        Raises:
            ValueError: If session not found / wrong company.
        """
        session = self.get_session(session_id, company_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or access denied")

        queries = (
            self.db.query(Query)
            .filter(
                Query.session_id == session_id,
                Query.company_id == company_id
            )
            .order_by(Query.turn_number.asc(), Query.created_at.asc())
            .all()
        )

        turns: List[SessionTurn] = []
        for q in queries:
            # Use the first (and usually only) result for this query
            result: Optional[QueryResult] = (
                self.db.query(QueryResult)
                .filter(QueryResult.query_id == q.id)
                .order_by(QueryResult.created_at.desc())
                .first()
            )

            viz_data = None
            if result:
                viz_data = VisualizationService.prepare_visualization_data(
                    results=result.results_data,
                    chart_type=result.chart_type
                )

            turns.append(SessionTurn(
                turn_number=q.turn_number or 0,
                query_id=q.id,
                natural_language_query=q.natural_language_query,
                generated_sql=q.generated_sql,
                result_id=result.id if result else None,
                chart_type=result.chart_type if result else None,
                ai_insight=result.ai_insight if result else None,
                visualization_data=viz_data,
                created_at=q.created_at
            ))

        return turns

    def get_latest_result(
        self,
        session_id: UUID,
        company_id: UUID
    ) -> Optional[QueryResult]:
        """
        Return the most recent QueryResult in the session.
        Uses the denormalized session_id on QueryResult for a single indexed query.

        Raises:
            ValueError: If session not found / wrong company.
        """
        session = self.get_session(session_id, company_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or access denied")

        return (
            self.db.query(QueryResult)
            .filter(
                QueryResult.session_id == session_id,
                QueryResult.company_id == company_id
            )
            .order_by(QueryResult.created_at.desc())
            .first()
        )

    def list_sessions(
        self,
        company_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Session]:
        """
        Return sessions for a company, newest first.
        """
        return (
            self.db.query(Session)
            .filter(Session.company_id == company_id)
            .order_by(Session.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def set_title_if_empty(
        self,
        session: Session,
        natural_language_query: str
    ) -> None:
        """
        If the session has no title yet, set it from the first query (trimmed to 80 chars).
        Commits the change.
        """
        if session.title:
            return
        session.title = natural_language_query[:80]
        self.db.commit()

    def next_turn_number(
        self,
        session_id: UUID
    ) -> int:
        """
        Return count_of_existing_queries + 1 for the given session.
        """
        count = (
            self.db.query(Query)
            .filter(Query.session_id == session_id)
            .count()
        )
        return count + 1

    def delete_session(
        self,
        session_id: UUID,
        company_id: UUID
    ) -> bool:
        """
        Delete a session. DB cascade handles child queries + results.

        Returns True if deleted, False if not found.
        """
        try:
            session = self.get_session(session_id, company_id)
            if not session:
                return False

            self.db.delete(session)
            self.db.commit()

            logger.info("Session deleted", session_id=str(session_id))
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to delete session", error=str(e))
            raise