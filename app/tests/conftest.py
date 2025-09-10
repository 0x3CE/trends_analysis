# conftest.py
"""Configuration des fixtures pytest pour les tests d'intégration."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.main import app
from app.database import Base, get_db
from app.services import tweet_service

# Configuration de la base de données de test en mémoire
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Crée et nettoie la base de données de test pour toute la session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Fournit une session de base de données isolée pour chaque test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Annule toutes les modifications après le test
        db.close()


@pytest.fixture
def client(db_session):
    """Fournit un client de test FastAPI avec injection de la base de données de test."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Nettoie les overrides après le test
        app.dependency_overrides.clear()


@pytest.fixture
def mock_twitter_client():
    """Mock du client Twitter avec données de test par défaut."""
    mock_client = Mock()
    mock_client.search_recent.return_value = {
        "data": [
            {
                "id": "123456789",
                "text": "Test tweet #python #fastapi",
                "author_id": "user123",
                "created_at": "2024-01-01T12:00:00.000Z"
            }
        ],
        "meta": {"result_count": 1}
    }
    
    with patch("app.services.tweet_service.twitter_client", mock_client):
        yield mock_client