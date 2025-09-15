# tests/conftest.py
"""Configuration des fixtures pytest pour les tests d'intégration."""
import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Ajout du répertoire parent au PYTHONPATH pour importer app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.database import Base, get_db
from app import models  # Import explicite pour enregistrer les modèles
from app.services import tweet_service

# Base de données complètement en mémoire - AUCUN fichier
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Désactive les logs SQL pour les tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Prépare l'environnement de test - base 100% en mémoire."""
    # Crée toutes les tables dans la base en mémoire
    Base.metadata.create_all(bind=test_engine)
    yield
    # Rien à nettoyer - la base disparaît automatiquement


@pytest.fixture(scope="function")
def db_session():
    """Session de base de données isolée pour chaque test."""
    # Crée une nouvelle connexion pour chaque test
    connection = test_engine.connect()
    
    # Démarre une transaction
    trans = connection.begin()
    
    # Session liée à cette transaction
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        # Ferme la session
        session.close()
        # Rollback de la transaction (annule tout)
        trans.rollback()
        # Ferme la connexion
        connection.close()


@pytest.fixture
def client(db_session):
    """Client de test FastAPI avec base de données en mémoire."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Remplace la dépendance de base de données
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Nettoie les overrides
        app.dependency_overrides.clear()


@pytest.fixture
def mock_twitter_client():
    """Mock du client Twitter avec données de test."""
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
