"""
Results Service
Handles storing and retrieving query results for visualization
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
import structlog


from app.models.query_result import QueryResult
from app.models.query import Query
from app.services.visualization_service import VisualizationService
from app.core.config import settings

logger = structlog.get_logger()


class ResultsService:
    """
    Service for managing query results and visualizations
    """

    def __init__(self, db: Session):
        self.db = db

    async def store_results(
        self,
        query_id: UUID,
        company_id: UUID,
        results_data: List[Dict[str, Any]],
        ai_client=None,
        session_id: Optional[UUID] = None
    ) -> QueryResult:
        """
        Store query results and auto-detect visualization

        Args:
            query_id: UUID of the original query
            company_id: Company ID for tenant isolation
            results_data: Array of result rows
            ai_client: Optional AI client for generating insights

        Returns:
            Created QueryResult object

        Raises:
            ValueError: If query not found or doesn't belong to company
            SQLAlchemyError: If database operation fails
        """
        try:
            # Verify query exists and belongs to company
            query = self.db.query(Query).filter(
                Query.id == query_id,
                Query.company_id == company_id
            ).first()

            if not query:
                raise ValueError(f"Query {query_id} not found or access denied")

            # Enforce row count limit
            row_count = len(results_data)
            if row_count > settings.RESULT_MAX_ROWS:
                raise ValueError(
                    f"Result set exceeds the maximum allowed row count of "
                    f"{settings.RESULT_MAX_ROWS:,} rows (received {row_count:,}). "
                    "Apply a LIMIT clause to reduce the result size."
                )

            # Enforce payload size limit
            result_bytes = len(json.dumps(results_data, default=str).encode("utf-8"))
            result_size_mb = result_bytes / (1024 * 1024)
            if result_size_mb > settings.RESULT_MAX_SIZE_MB:
                raise ValueError(
                    f"Result payload size ({result_size_mb:.1f} MB) exceeds the maximum "
                    f"allowed size of {settings.RESULT_MAX_SIZE_MB} MB. "
                    "Reduce the number of rows or columns returned."
                )

            # Calculate metadata
            column_count = len(results_data[0].keys()) if results_data else 0

            # Auto-detect chart type
            chart_type = VisualizationService.detect_chart_type(results_data)

            logger.info(
                "Storing query results",
                query_id=str(query_id),
                row_count=row_count,
                column_count=column_count,
                chart_type=chart_type
            )

            # Generate AI insight if client provided
            ai_insight = None
            if ai_client and results_data:
                ai_insight = await VisualizationService.generate_ai_insight(
                    query=query.natural_language_query,
                    results=results_data,
                    chart_type=chart_type,
                    ai_client=ai_client
                )

            # Create query result
            query_result = QueryResult(
                query_id=query_id,
                company_id=company_id,
                session_id=session_id,
                results_data=results_data,
                row_count=row_count,
                column_count=column_count,
                chart_type=chart_type,
                ai_insight=ai_insight,
                is_public=False  # Private by default
            )

            self.db.add(query_result)
            self.db.commit()
            self.db.refresh(query_result)

            logger.info(
                "Query results stored successfully",
                result_id=str(query_result.id),
                chart_type=chart_type
            )

            return query_result

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to store query results", error=str(e))
            raise

    def get_result(
        self,
        result_id: UUID,
        company_id: Optional[UUID] = None
    ) -> Optional[QueryResult]:
        """
        Retrieve query result by ID

        Args:
            result_id: UUID of the query result
            company_id: Optional company ID for access control (None = public access)

        Returns:
            QueryResult object or None if not found
        """
        try:
            query = self.db.query(QueryResult).filter(
                QueryResult.id == result_id
            )

            # If company_id provided, enforce tenant isolation
            # If not provided, only allow public results
            if company_id:
                query = query.filter(QueryResult.company_id == company_id)
            else:
                query = query.filter(QueryResult.is_public == True)

            result = query.first()

            if result:
                logger.info("Query result retrieved", result_id=str(result_id))
            else:
                logger.warning("Query result not found or access denied", result_id=str(result_id))

            return result

        except SQLAlchemyError as e:
            logger.error("Failed to retrieve query result", error=str(e))
            return None

    def list_results(
        self,
        company_id: UUID,
        query_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[QueryResult]:
        """
        List query results for a company

        Args:
            company_id: Company ID for tenant isolation
            query_id: Optional filter by specific query
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of QueryResult objects
        """
        try:
            query = self.db.query(QueryResult).filter(
                QueryResult.company_id == company_id
            )

            if query_id:
                query = query.filter(QueryResult.query_id == query_id)

            results = query.order_by(
                QueryResult.created_at.desc()
            ).limit(limit).offset(offset).all()

            logger.info(
                "Listed query results",
                company_id=str(company_id),
                count=len(results)
            )

            return results

        except SQLAlchemyError as e:
            logger.error("Failed to list query results", error=str(e))
            return []

    def make_public(
        self,
        result_id: UUID,
        company_id: UUID,
        is_public: bool = True,
        share_expires_at=None,
    ) -> Optional[QueryResult]:
        """
        Make a query result public or private

        Args:
            result_id: UUID of the query result
            company_id: Company ID for access control
            is_public: Whether to make public (True) or private (False)

        Returns:
            Updated QueryResult or None if not found
        """
        try:
            result = self.db.query(QueryResult).filter(
                QueryResult.id == result_id,
                QueryResult.company_id == company_id
            ).first()

            if not result:
                logger.warning("Query result not found", result_id=str(result_id))
                return None

            result.is_public = is_public
            if is_public:
                result.share_expires_at = share_expires_at
            else:
                result.share_expires_at = None  # clear expiry when making private
            self.db.commit()
            self.db.refresh(result)

            logger.info(
                "Query result sharing updated",
                result_id=str(result_id),
                is_public=is_public
            )

            return result

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to update sharing settings", error=str(e))
            return None

    def delete_result(
        self,
        result_id: UUID,
        company_id: UUID
    ) -> bool:
        """
        Delete a query result

        Args:
            result_id: UUID of the query result
            company_id: Company ID for access control

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.db.query(QueryResult).filter(
                QueryResult.id == result_id,
                QueryResult.company_id == company_id
            ).first()

            if not result:
                logger.warning("Query result not found", result_id=str(result_id))
                return False

            self.db.delete(result)
            self.db.commit()

            logger.info("Query result deleted", result_id=str(result_id))
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to delete query result", error=str(e))
            return False