# tests/test_integration_api.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.models import Tweet
from app.exceptions import TwitterAPIError
from app.services.tweet_service import TweetService

# Helper pour parser ISO8601
def iso(dt: str):
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))

# --- Tests API avec injection de mock Twitter client --- #

@pytest.fixture
def mock_twitter_client_patch(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr("app.services.tweet_service.twitter_client", mock_client)
    return mock_client


def test_collect_tweets_success(client, db_session, mock_twitter_client_patch):
    """Test /tweets/collect avec des données valides"""
    mock_twitter_client_patch.search_recent.return_value = {
        "data": [
            {"id": "1", "text": "Hello #Python #FastAPI", "author_id": "user1", "created_at": "2025-01-01T10:00:00.000Z"},
            {"id": "2", "text": "Another test", "author_id": "user2", "created_at": "2025-01-01T11:00:00.000Z"}
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
    """Test /tweets/collect avec query vide"""
    response = client.post("/tweets/collect", json={"query": ""})
    assert response.status_code == 422
    assert "query" in response.json()["detail"][0]["loc"]


def test_collect_tweets_api_error(client, mock_twitter_client_patch):
    """Simule une erreur API Twitter"""
    mock_twitter_client_patch.search_recent.side_effect = TwitterAPIError("Simulated API error")
    response = client.post("/tweets/collect", json={"query": "error"})
    assert response.status_code == 502
    assert "Twitter API error" in response.json()["detail"]


def test_list_tweets_success(client, db_session):
    """Test /tweets avec des tweets existants"""
    db_session.add(Tweet(tweet_id="100", text="Test tweet 1", created_at=iso("2025-01-01T10:00:00Z")))
    db_session.add(Tweet(tweet_id="101", text="Test tweet 2", created_at=iso("2025-01-01T11:00:00Z")))
    db_session.commit()

    response = client.get("/tweets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "101"  # tri par created_at desc


def test_list_tweets_limit(client, db_session):
    """Test param limit sur /tweets"""
    db_session.add(Tweet(tweet_id="102", text="Tweet 1", created_at=iso("2025-01-01T12:00:00Z")))
    db_session.add(Tweet(tweet_id="103", text="Tweet 2", created_at=iso("2025-01-01T12:30:00Z")))
    db_session.add(Tweet(tweet_id="104", text="Tweet 3", created_at=iso("2025-01-01T13:00:00Z")))
    db_session.commit()

    response = client.get("/tweets/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "104"
    assert data[1]["tweet_id"] == "103"


def test_list_tweets_database_empty(client):
    """Test /tweets avec DB vide"""
    response = client.get("/tweets/")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_top_hashtags_success(client, db_session):
    """Test /analytics/hashtags"""
    db_session.add(Tweet(tweet_id="200", text="A tweet with #PyTest and #FastAPI", created_at=iso("2025-01-01T10:00:00Z")))
    db_session.add(Tweet(tweet_id="201", text="Another tweet with #FastAPI", created_at=iso("2025-01-01T11:00:00Z")))
    db_session.add(Tweet(tweet_id="202", text="A third tweet with no hashtags", created_at=iso("2025-01-01T12:00:00Z")))
    db_session.commit()

    response = client.get("/analytics/hashtags")
    assert response.status_code == 200
    data = response.json()["top_hashtags"]
    assert len(data) == 2
    assert data[0]["hashtag"] == "#fastapi"
    assert data[0]["count"] == 2
    assert data[1]["hashtag"] == "#pytest"
    assert data[1]["count"] == 1


def test_get_top_hashtags_empty_db(client):
    """Test analytics hashtags avec DB vide"""
    response = client.get("/analytics/hashtags")
    assert response.status_code == 200
    assert response.json()["top_hashtags"] == []


def test_get_volume_by_hour_success(client, db_session):
    """Test /analytics/volume_by_hour"""
    db_session.add(Tweet(tweet_id="300", text="t1", created_at=iso("2025-01-01T10:00:00.000Z")))
    db_session.add(Tweet(tweet_id="301", text="t2", created_at=iso("2025-01-01T10:30:00.000Z")))
    db_session.add(Tweet(tweet_id="302", text="t3", created_at=iso("2025-01-01T11:00:00.000Z")))
    db_session.commit()

    response = client.get("/analytics/volume_by_hour")
    assert response.status_code == 200
    data = response.json()["volume_by_hour"]
    assert len(data) == 2
    assert data[0]["hour_or_key"] == "2025-01-01T10"
    assert data[0]["count"] == 2
    assert data[1]["hour_or_key"] == "2025-01-01T11"
    assert data[1]["count"] == 1


def test_get_volume_by_hour_empty_db(client):
    """Test analytics volume par heure avec DB vide"""
    response = client.get("/analytics/volume_by_hour")
    assert response.status_code == 200
    assert response.json()["volume_by_hour"] == []


def test_simple_load_test(client, mock_twitter_client_patch):
    """Insertion rapide de 100 tweets simulés"""
    mock_data = {
        "data": [
            {"id": f"load_test_{i}", "text": f"Load test tweet #{i}", "author_id": "load_user", "created_at": "2025-01-01T12:00:00.000Z"}
            for i in range(100)
        ],
        "meta": {"result_count": 100}
    }

    mock_twitter_client_patch.search_recent.return_value = mock_data
    response = client.post("/tweets/collect", json={"query": "load_test", "max_results": 100})
    assert response.status_code == 200
    assert len(response.json()) == 100

    response = client.get("/tweets/", params={"limit": 1000})
    assert response.status_code == 200
    assert len(response.json()) > 0
