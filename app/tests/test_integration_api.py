# tests/test_integration_api.py (version finale)
"""Tests d'intégration de l'API - version sans fichiers."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from app.models import Tweet
from app.exceptions import TwitterAPIError


def parse_iso_date(date_string: str) -> datetime:
    """Parse une date ISO8601 en datetime Python."""
    return datetime.fromisoformat(date_string.replace("Z", "+00:00"))


@pytest.fixture
def mock_twitter_client_patch(monkeypatch):
    """Mock du client Twitter via monkeypatch."""
    mock_client = MagicMock()
    monkeypatch.setattr("app.services.tweet_service.twitter_client", mock_client)
    return mock_client


def test_collect_tweets_success(client, db_session, mock_twitter_client_patch):
    """Test de collecte de tweets avec succès."""
    mock_twitter_client_patch.search_recent.return_value = {
        "data": [
            {
                "id": "1", 
                "text": "Hello #Python #FastAPI", 
                "author_id": "user1", 
                "created_at": "2025-01-01T10:00:00.000Z"
            },
            {
                "id": "2", 
                "text": "Another test", 
                "author_id": "user2", 
                "created_at": "2025-01-01T11:00:00.000Z"
            }
        ],
        "meta": {"result_count": 2}
    }

    response = client.post("/tweets/collect", json={"query": "test", "max_results": 10})
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "1"
    assert data[1]["tweet_id"] == "2"


def test_collect_tweets_empty_query(client):
    """Test avec une query vide."""
    response = client.post("/tweets/collect", json={"query": ""})
    assert response.status_code == 422


def test_collect_tweets_api_error(client, mock_twitter_client_patch):
    """Test avec erreur API Twitter."""
    mock_twitter_client_patch.search_recent.side_effect = TwitterAPIError("Simulated API error")
    
    response = client.post("/tweets/collect", json={"query": "error"})
    assert response.status_code == 502
    
    error_detail = response.json()["detail"].lower()
    assert any(word in error_detail for word in ["twitter", "api", "error"])


def test_list_tweets_success(client, db_session):
    """Test de récupération de tweets existants."""
    tweet1 = Tweet(
        tweet_id="100", 
        text="Test tweet 1", 
        created_at=parse_iso_date("2025-01-01T10:00:00Z")
    )
    tweet2 = Tweet(
        tweet_id="101", 
        text="Test tweet 2", 
        created_at=parse_iso_date("2025-01-01T11:00:00Z")
    )
    
    db_session.add(tweet1)
    db_session.add(tweet2)
    db_session.commit()

    response = client.get("/tweets/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "101"


def test_list_tweets_limit(client, db_session):
    """Test du paramètre limit."""
    tweets = [
        Tweet(tweet_id="102", text="Tweet 1", created_at=parse_iso_date("2025-01-01T12:00:00Z")),
        Tweet(tweet_id="103", text="Tweet 2", created_at=parse_iso_date("2025-01-01T12:30:00Z")),
        Tweet(tweet_id="104", text="Tweet 3", created_at=parse_iso_date("2025-01-01T13:00:00Z"))
    ]
    
    for tweet in tweets:
        db_session.add(tweet)
    db_session.commit()

    response = client.get("/tweets/?limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "104"
    assert data[1]["tweet_id"] == "103"


def test_list_tweets_database_empty(client):
    """Test avec base de données vide."""
    response = client.get("/tweets/")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_top_hashtags_success(client, db_session):
    """Test des analytics de hashtags."""
    tweets = [
        Tweet(tweet_id="200", text="A tweet with #PyTest and #FastAPI", created_at=parse_iso_date("2025-01-01T10:00:00Z")),
        Tweet(tweet_id="201", text="Another tweet with #FastAPI", created_at=parse_iso_date("2025-01-01T11:00:00Z")),
        Tweet(tweet_id="202", text="A third tweet with no hashtags", created_at=parse_iso_date("2025-01-01T12:00:00Z"))
    ]
    
    for tweet in tweets:
        db_session.add(tweet)
    db_session.commit()

    response = client.get("/analytics/hashtags")
    assert response.status_code == 200
    
    data = response.json()["top_hashtags"]
    assert len(data) >= 1
    
    fastapi_found = any(
        hashtag["hashtag"].lower() == "#fastapi" 
        for hashtag in data
    )
    assert fastapi_found


def test_get_top_hashtags_empty_db(client):
    """Test hashtags avec DB vide."""
    response = client.get("/analytics/hashtags")
    assert response.status_code == 200
    assert response.json()["top_hashtags"] == []


def test_get_volume_by_hour_success(client, db_session):
    """Test du volume par heure."""
    tweets = [
        Tweet(tweet_id="300", text="t1", created_at=parse_iso_date("2025-01-01T10:00:00Z")),
        Tweet(tweet_id="301", text="t2", created_at=parse_iso_date("2025-01-01T10:30:00Z")),
        Tweet(tweet_id="302", text="t3", created_at=parse_iso_date("2025-01-01T11:00:00Z"))
    ]
    
    for tweet in tweets:
        db_session.add(tweet)
    db_session.commit()

    response = client.get("/analytics/volume_by_hour")
    assert response.status_code == 200
    
    data = response.json()["volume_by_hour"]
    assert len(data) >= 1


def test_get_volume_by_hour_empty_db(client):
    """Test volume par heure avec DB vide."""
    response = client.get("/analytics/volume_by_hour")
    assert response.status_code == 200
    assert response.json()["volume_by_hour"] == []


def test_simple_load_test(client, mock_twitter_client_patch):
    """Test de charge avec 100 tweets - version sans fichiers."""
    mock_data = {
        "data": [
            {
                "id": f"load_test_{i}", 
                "text": f"Load test tweet #{i}", 
                "author_id": "load_user", 
                "created_at": "2025-01-01T12:00:00.000Z"
            }
            for i in range(100)
        ],
        "meta": {"result_count": 100}
    }

    mock_twitter_client_patch.search_recent.return_value = mock_data
    
    response = client.post("/tweets/collect", json={"query": "load_test", "max_results": 100})
    assert response.status_code == 200
    
    collected_tweets = response.json()
    assert len(collected_tweets) > 0
    
    response = client.get("/tweets/", params={"limit": 1000})
    assert response.status_code == 200
    assert len(response.json()) > 0