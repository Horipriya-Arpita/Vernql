"""
Example Manager Service
Manages query examples for few-shot learning and query improvement
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import structlog

from app.models.query_example import QueryExample, ExampleSource
from app.services.prompt_builder import Example

logger = structlog.get_logger()


class ExampleManager:
    """
    Manages query examples for few-shot learning

    Features:
    - Store and retrieve examples
    - Find relevant examples for a query
    - Track example usage and success
    - Auto-generate examples from successful queries
    """

    def __init__(self):
        self.logger = logger.bind(service="example_manager")

    def create_example(
        self,
        db: Session,
        company_id: str,
        natural_language: str,
        sql_query: str,
        schema_id: Optional[str] = None,
        explanation: Optional[str] = None,
        source: ExampleSource = ExampleSource.MANUAL,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> QueryExample:
        """
        Create a new query example

        Args:
            db: Database session
            company_id: Company ID
            natural_language: Natural language query
            sql_query: SQL query
            schema_id: Optional schema ID
            explanation: Optional explanation
            source: Source of example
            tags: Optional tags for categorization
            difficulty: Optional difficulty level
            quality_score: Optional quality score (1-10)

        Returns:
            Created QueryExample
        """
        example = QueryExample(
            company_id=company_id,
            schema_id=schema_id,
            natural_language=natural_language,
            sql_query=sql_query,
            explanation=explanation,
            source=source,
            tags=",".join(tags) if tags else None,
            difficulty=difficulty,
            quality_score=quality_score,
            is_verified=(source == ExampleSource.CURATED)
        )

        db.add(example)
        db.commit()
        db.refresh(example)

        self.logger.info(
            "Example created",
            example_id=str(example.id),
            source=source.value
        )

        return example

    def get_examples_for_schema(
        self,
        db: Session,
        schema_id: str,
        company_id: str,
        limit: int = 5,
        only_verified: bool = False
    ) -> List[QueryExample]:
        """
        Get examples for a specific schema

        Args:
            db: Database session
            schema_id: Schema ID
            company_id: Company ID
            limit: Maximum number of examples
            only_verified: Only return verified examples

        Returns:
            List of QueryExample objects
        """
        query = db.query(QueryExample).filter(
            QueryExample.schema_id == schema_id,
            QueryExample.company_id == company_id,
            QueryExample.is_active == True
        )

        if only_verified:
            query = query.filter(QueryExample.is_verified == True)

        # Order by quality and usage
        examples = query.order_by(
            QueryExample.quality_score.desc().nullslast(),
            QueryExample.usage_count.desc()
        ).limit(limit).all()

        return examples

    def find_relevant_examples(
        self,
        db: Session,
        company_id: str,
        natural_language_query: str,
        schema_id: Optional[str] = None,
        limit: int = 3
    ) -> List[Example]:
        """
        Find relevant examples for a query using keyword matching

        Args:
            db: Database session
            company_id: Company ID
            natural_language_query: User's query
            schema_id: Optional schema ID to filter by
            limit: Maximum number of examples

        Returns:
            List of Example objects for prompt building
        """
        # Extract keywords from query
        keywords = self._extract_keywords(natural_language_query)

        # Build query
        query = db.query(QueryExample).filter(
            QueryExample.company_id == company_id,
            QueryExample.is_active == True
        )

        if schema_id:
            # Prefer schema-specific examples, but include global ones too
            query = query.filter(
                (QueryExample.schema_id == schema_id) |
                (QueryExample.schema_id == None)
            )

        # Get all active examples
        all_examples = query.all()

        # Score examples by keyword relevance
        scored_examples = []
        for example in all_examples:
            score = self._calculate_relevance_score(
                example.natural_language,
                example.tags or "",
                keywords
            )
            scored_examples.append((score, example))

        # Sort by score and take top N
        scored_examples.sort(reverse=True, key=lambda x: x[0])
        top_examples = [ex for _, ex in scored_examples[:limit] if _ > 0]

        # Convert to Example objects for prompt builder
        result = [
            Example(
                natural_language=ex.natural_language,
                sql=ex.sql_query,
                explanation=ex.explanation
            )
            for ex in top_examples
        ]

        # Increment usage count
        for _, ex in scored_examples[:limit]:
            ex.usage_count += 1
        db.commit()

        self.logger.debug(
            "Found relevant examples",
            count=len(result),
            query_preview=natural_language_query[:50]
        )

        return result

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about',
            'into', 'through', 'during', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'show', 'get', 'find', 'list', 'give', 'me', 'all'
        }

        words = text.lower().split()
        keywords = {w for w in words if w not in stop_words and len(w) > 2}

        return keywords

    def _calculate_relevance_score(
        self,
        example_text: str,
        tags: str,
        query_keywords: set
    ) -> float:
        """Calculate relevance score between example and query"""
        # Convert example to keywords
        example_keywords = self._extract_keywords(example_text)

        # Check tag matches
        tag_keywords = set(tags.lower().split(',')) if tags else set()

        # Calculate overlap
        text_overlap = len(query_keywords & example_keywords)
        tag_overlap = len(query_keywords & tag_keywords)

        # Weight tags more heavily
        score = text_overlap + (tag_overlap * 2)

        return score

    def mark_example_success(
        self,
        db: Session,
        example_id: str,
        success: bool
    ):
        """
        Mark an example as successful or failed

        Args:
            db: Database session
            example_id: Example ID
            success: Whether the example led to successful query
        """
        example = db.query(QueryExample).filter(
            QueryExample.id == example_id
        ).first()

        if not example:
            return

        # Update success rate
        if example.success_rate is None:
            example.success_rate = 100 if success else 0
        else:
            # Moving average
            alpha = 0.1  # Weight for new observation
            new_value = 100 if success else 0
            example.success_rate = int(
                alpha * new_value + (1 - alpha) * example.success_rate
            )

        db.commit()

    def auto_create_example_from_query(
        self,
        db: Session,
        company_id: str,
        schema_id: str,
        natural_language: str,
        sql_query: str,
        confidence_score: float,
        min_confidence: float = 0.9
    ) -> Optional[QueryExample]:
        """
        Automatically create example from successful query

        Args:
            db: Database session
            company_id: Company ID
            schema_id: Schema ID
            natural_language: Natural language query
            sql_query: Generated SQL
            confidence_score: Confidence score
            min_confidence: Minimum confidence to auto-create

        Returns:
            Created example or None
        """
        # Only create examples from high-confidence queries
        if confidence_score < min_confidence:
            return None

        # Check if similar example already exists
        existing = db.query(QueryExample).filter(
            QueryExample.company_id == company_id,
            QueryExample.schema_id == schema_id,
            QueryExample.natural_language == natural_language
        ).first()

        if existing:
            # Update existing
            existing.usage_count += 1
            db.commit()
            return existing

        # Create new example
        example = self.create_example(
            db=db,
            company_id=company_id,
            schema_id=schema_id,
            natural_language=natural_language,
            sql_query=sql_query,
            source=ExampleSource.AUTO_GENERATED,
            quality_score=int(confidence_score * 10)
        )

        self.logger.info(
            "Auto-created example from successful query",
            example_id=str(example.id),
            confidence=confidence_score
        )

        return example

    def get_example_stats(
        self,
        db: Session,
        company_id: str,
        schema_id: Optional[str] = None
    ) -> Dict:
        """
        Get statistics about examples

        Args:
            db: Database session
            company_id: Company ID
            schema_id: Optional schema ID

        Returns:
            Dictionary of statistics
        """
        query = db.query(QueryExample).filter(
            QueryExample.company_id == company_id
        )

        if schema_id:
            query = query.filter(QueryExample.schema_id == schema_id)

        total = query.count()
        active = query.filter(QueryExample.is_active == True).count()
        verified = query.filter(QueryExample.is_verified == True).count()

        # Average quality score
        avg_quality = db.query(
            func.avg(QueryExample.quality_score)
        ).filter(
            QueryExample.company_id == company_id,
            QueryExample.quality_score != None
        ).scalar() or 0

        return {
            "total": total,
            "active": active,
            "verified": verified,
            "average_quality": round(avg_quality, 2)
        }

    def delete_example(
        self,
        db: Session,
        example_id: str,
        company_id: str
    ) -> bool:
        """
        Soft delete an example

        Args:
            db: Database session
            example_id: Example ID
            company_id: Company ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        example = db.query(QueryExample).filter(
            QueryExample.id == example_id,
            QueryExample.company_id == company_id
        ).first()

        if not example:
            return False

        example.is_active = False
        db.commit()

        self.logger.info("Example deleted", example_id=example_id)
        return True

    def bulk_import_examples(
        self,
        db: Session,
        company_id: str,
        schema_id: str,
        examples: List[Dict]
    ) -> int:
        """
        Bulk import examples

        Args:
            db: Database session
            company_id: Company ID
            schema_id: Schema ID
            examples: List of example dictionaries

        Returns:
            Number of examples imported
        """
        count = 0
        for ex_data in examples:
            try:
                self.create_example(
                    db=db,
                    company_id=company_id,
                    schema_id=schema_id,
                    natural_language=ex_data.get("natural_language"),
                    sql_query=ex_data.get("sql_query"),
                    explanation=ex_data.get("explanation"),
                    tags=ex_data.get("tags"),
                    difficulty=ex_data.get("difficulty"),
                    quality_score=ex_data.get("quality_score")
                )
                count += 1
            except Exception as e:
                self.logger.error("Failed to import example", error=str(e))

        self.logger.info(f"Bulk imported {count} examples")
        return count
