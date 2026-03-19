"""
Tests for SQL Generator
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.sql_generator import SQLGenerator, SQLGenerationResult
from app.services.ai_provider import BaseAIProvider
from app.models import Schema, SchemaTable, SchemaColumn, DatabaseType, QueryExample, ExampleSource
from uuid import uuid4


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing"""

    def __init__(self, mock_response: str = "SELECT * FROM users LIMIT 100;"):
        self.mock_response = mock_response
        self.model = "mock-model"
        self.provider_name = "mock"

    async def simple_completion(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        return self.mock_response

    def get_provider_name(self) -> str:
        return self.provider_name


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing"""
    schema = Schema(
        id=uuid4(),
        company_id=uuid4(),
        name="test_db",
        db_type=DatabaseType.POSTGRESQL,
        is_active=True,
        enriched_description="Test database for e-commerce"
    )

    # Users table
    users_table = SchemaTable(
        id=uuid4(),
        schema_id=schema.id,
        name="users",
        enriched_description="Customer accounts and profiles"
    )

    users_table.columns = [
        SchemaColumn(
            id=uuid4(),
            table_id=users_table.id,
            name="id",
            data_type="INTEGER",
            is_primary_key=True,
            is_nullable=False,
            enriched_description="Unique user identifier"
        ),
        SchemaColumn(
            id=uuid4(),
            table_id=users_table.id,
            name="email",
            data_type="VARCHAR(255)",
            is_nullable=False,
            enriched_description="User email address"
        ),
        SchemaColumn(
            id=uuid4(),
            table_id=users_table.id,
            name="created_at",
            data_type="TIMESTAMP",
            is_nullable=False,
            enriched_description="Account creation timestamp"
        ),
    ]

    # Orders table
    orders_table = SchemaTable(
        id=uuid4(),
        schema_id=schema.id,
        name="orders",
        enriched_description="Customer order records"
    )

    orders_table.columns = [
        SchemaColumn(
            id=uuid4(),
            table_id=orders_table.id,
            name="id",
            data_type="INTEGER",
            is_primary_key=True,
            is_nullable=False,
            enriched_description="Unique order identifier"
        ),
        SchemaColumn(
            id=uuid4(),
            table_id=orders_table.id,
            name="user_id",
            data_type="INTEGER",
            is_foreign_key=True,
            foreign_key_table="users",
            is_nullable=False,
            enriched_description="Reference to user who placed the order"
        ),
        SchemaColumn(
            id=uuid4(),
            table_id=orders_table.id,
            name="total",
            data_type="DECIMAL(10,2)",
            is_nullable=False,
            enriched_description="Total order amount"
        ),
        SchemaColumn(
            id=uuid4(),
            table_id=orders_table.id,
            name="status",
            data_type="VARCHAR(50)",
            is_nullable=False,
            enriched_description="Order status (pending, completed, cancelled)"
        ),
    ]

    schema.tables = [users_table, orders_table]
    return schema


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = Mock()
    return db


class TestSQLGenerator:
    """Test suite for SQLGenerator"""

    def test_initialization(self):
        """Test generator initialization"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        assert generator.ai_provider is not None
        assert generator.validator is not None
        assert generator.example_manager is not None
        assert generator.use_examples == False

    def test_initialization_default_provider(self):
        """Test generator with default provider"""
        with patch('app.services.sql_generator.AIProviderFactory.create_from_settings') as mock_factory:
            mock_factory.return_value = MockAIProvider()
            generator = SQLGenerator()

            assert generator.ai_provider is not None
            mock_factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sql_simple_query(self, sample_schema, mock_db):
        """Test SQL generation for simple query"""
        provider = MockAIProvider("SELECT * FROM users LIMIT 100;")
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_schema
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = await generator.generate_sql(
            db=mock_db,
            schema_id=str(sample_schema.id),
            natural_language_query="Show all users",
            company_id=str(sample_schema.company_id)
        )

        assert isinstance(result, SQLGenerationResult)
        assert "SELECT" in result.sql.upper()
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_generate_sql_with_validation_errors(self, sample_schema, mock_db):
        """Test SQL generation with dangerous keywords"""
        provider = MockAIProvider("DROP TABLE users;")
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        mock_db.query.return_value.filter.return_value.first.return_value = sample_schema

        result = await generator.generate_sql(
            db=mock_db,
            schema_id=str(sample_schema.id),
            natural_language_query="Delete all users",
            company_id=str(sample_schema.company_id)
        )

        # Should have warnings about forbidden keywords
        assert len(result.warnings) > 0
        assert any("DROP" in warning.upper() for warning in result.warnings)
        # Confidence should be very low due to errors
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_generate_sql_schema_not_found(self, mock_db):
        """Test error when schema not found"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found or inaccessible"):
            await generator.generate_sql(
                db=mock_db,
                schema_id=str(uuid4()),
                natural_language_query="Show all users",
                company_id=str(uuid4())
            )

    @pytest.mark.asyncio
    async def test_generate_sql_with_examples(self, sample_schema, mock_db):
        """Test SQL generation with example-based learning"""
        provider = MockAIProvider("SELECT email FROM users WHERE created_at > '2023-01-01' LIMIT 100;")
        generator = SQLGenerator(ai_provider=provider, use_examples=True)

        mock_db.query.return_value.filter.return_value.first.return_value = sample_schema
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.all.return_value = []
        mock_db.add = Mock()
        mock_db.commit = Mock()

        result = await generator.generate_sql(
            db=mock_db,
            schema_id=str(sample_schema.id),
            natural_language_query="Show users created this year",
            company_id=str(sample_schema.company_id)
        )

        assert isinstance(result, SQLGenerationResult)
        assert result.confidence > 0.0

    def test_parse_ai_response_clean_sql(self):
        """Test parsing clean SQL response"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        response = "SELECT * FROM users LIMIT 100;"
        result = generator._parse_ai_response(response)

        assert "SELECT" in result.sql.upper()
        assert not result.sql.endswith(';')  # Semicolon should be removed

    def test_parse_ai_response_with_markdown(self):
        """Test parsing SQL wrapped in markdown"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        response = "```sql\nSELECT * FROM users LIMIT 100;\n```"
        result = generator._parse_ai_response(response)

        assert "SELECT" in result.sql.upper()
        assert "```" not in result.sql

    def test_parse_ai_response_with_explanation(self):
        """Test parsing SQL with extra text"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        response = "Here's the SQL query:\nSELECT * FROM users LIMIT 100;"
        result = generator._parse_ai_response(response)

        # Should extract just the SQL
        assert "SELECT" in result.sql.upper()

    def test_calculate_confidence_high_quality(self, sample_schema):
        """Test confidence calculation for high-quality query"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        result = SQLGenerationResult(
            sql="SELECT id, email FROM users WHERE created_at > '2023-01-01' LIMIT 100",
            confidence=0.0,
            warnings=[]
        )

        confidence = generator._calculate_confidence(
            result=result,
            schema=sample_schema,
            query="Show users created this year",
            has_validation_errors=False
        )

        # Should have high confidence
        assert confidence > 0.7

    def test_calculate_confidence_with_errors(self, sample_schema):
        """Test confidence calculation with validation errors"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        result = SQLGenerationResult(
            sql="DROP TABLE users;",
            confidence=0.0,
            warnings=["Forbidden keyword: DROP"]
        )

        confidence = generator._calculate_confidence(
            result=result,
            schema=sample_schema,
            query="Delete all users",
            has_validation_errors=True
        )

        # Should have very low confidence
        assert confidence <= 0.3

    def test_calculate_confidence_with_warnings(self, sample_schema):
        """Test confidence calculation with warnings"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        result = SQLGenerationResult(
            sql="SELECT * FROM users",  # Missing LIMIT
            confidence=0.0,
            warnings=["Warning: No LIMIT clause"]
        )

        confidence = generator._calculate_confidence(
            result=result,
            schema=sample_schema,
            query="Show all users",
            has_validation_errors=False
        )

        # Should have moderate confidence (warnings reduce it slightly)
        assert 0.5 <= confidence < 1.0

    def test_calculate_confidence_unenriched_schema(self):
        """Test confidence reduction for unenriched schema"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        schema = Schema(
            id=uuid4(),
            company_id=uuid4(),
            name="test_db",
            db_type=DatabaseType.POSTGRESQL,
            is_active=True,
            enriched_description=None  # Not enriched
        )
        schema.tables = []

        result = SQLGenerationResult(
            sql="SELECT * FROM users LIMIT 100",
            confidence=0.0,
            warnings=[]
        )

        confidence = generator._calculate_confidence(
            result=result,
            schema=schema,
            query="Show all users",
            has_validation_errors=False
        )

        # Should be reduced due to lack of enrichment
        assert confidence < 1.0

    @pytest.mark.asyncio
    async def test_store_query_result(self, mock_db):
        """Test storing query result in database"""
        from app.models import QueryStatus

        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        mock_query = Mock()
        mock_query.id = uuid4()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(mock_query, 'id', uuid4()))

        with patch('app.services.sql_generator.Query', return_value=mock_query):
            result = await generator.store_query_result(
                db=mock_db,
                company_id=str(uuid4()),
                schema_id=str(uuid4()),
                natural_language_query="Show all users",
                generated_sql="SELECT * FROM users LIMIT 100;",
                confidence=0.95,
                status=QueryStatus.SUCCESS
            )

            assert mock_db.add.called
            assert mock_db.commit.called

    def test_sql_formatting(self):
        """Test SQL formatting with sqlparse"""
        provider = MockAIProvider()
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        messy_sql = "select id,email from users where created_at>'2023-01-01' limit 100"
        result = generator._parse_ai_response(messy_sql)

        # Should be formatted nicely
        assert "SELECT" in result.sql  # Keywords uppercased
        assert "\n" in result.sql or "  " in result.sql  # Some formatting applied

    @pytest.mark.asyncio
    async def test_complex_query_confidence(self, sample_schema, mock_db):
        """Test confidence for complex query"""
        complex_sql = """
        SELECT
            u.email,
            COUNT(o.id) as order_count,
            SUM(o.total) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.created_at >= '2023-01-01'
        GROUP BY u.id, u.email
        HAVING COUNT(o.id) > 5
        ORDER BY total_spent DESC
        LIMIT 50;
        """

        provider = MockAIProvider(complex_sql)
        generator = SQLGenerator(ai_provider=provider, use_examples=False)

        mock_db.query.return_value.filter.return_value.first.return_value = sample_schema
        mock_db.add = Mock()
        mock_db.commit = Mock()

        result = await generator.generate_sql(
            db=mock_db,
            schema_id=str(sample_schema.id),
            natural_language_query="Show top users by spending with more than 5 orders this year",
            company_id=str(sample_schema.company_id)
        )

        # Complex but valid query should have good confidence
        assert result.confidence > 0.5
        assert "JOIN" in result.sql.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
