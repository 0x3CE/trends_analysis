# app/tests/conftest.py
"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from app.main import app
from app.database import get_db, Base
from app.services.twitter_client import twitter_client


# Base de données en mémoire pour les tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Fixture pour créer une session de base de données de test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Fixture pour créer un client de test FastAPI."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Correction : retire le mot-clé 'app='
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_twitter_client():
    """Fixture pour mocker le client Twitter."""
    mock_client = Mock()
    mock_client.search_recent.return_value = {
        "data": [
            {
                "id": "123456789",
                "text": "Test tweet #python #fastapi",
                "author_id": "user123",
                "created_at": "2024-01-01T12:00:00.000Z"
            }
        ]
    }
    return mock_client