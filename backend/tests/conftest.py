"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings


# Use actual PostgreSQL for tests (since we have UUID types)
# Create a separate test database by changing only the database name
import re
TEST_DATABASE_URL = re.sub(r'/[^/]+$', '/textsql_test', settings.DATABASE_URL)

engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create and drop test database for the entire test session"""
    # Create test database
    main_engine = create_engine(settings.DATABASE_URL.rsplit('/', 1)[0] + '/postgres')
    with main_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        # Drop if exists
        conn.execute(text("DROP DATABASE IF EXISTS textsql_test"))
        # Create fresh
        conn.execute(text("CREATE DATABASE textsql_test"))
    main_engine.dispose()

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    with main_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("DROP DATABASE IF EXISTS textsql_test"))
    main_engine.dispose()


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_api_key():
    """Sample API key for testing"""
    return "textsql_test_key_12345678"


@pytest.fixture
def db(db_session):
    """Alias for db_session fixture for convenience"""
    return db_session
