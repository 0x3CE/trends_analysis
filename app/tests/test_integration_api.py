# tests/test_integration_api.py
import pytest
from unittest.mock import patch, MagicMock
from app.models import Tweet
from app.exceptions import TwitterAPIError


# The 'client', 'db_session', and 'mock_twitter_client' fixtures are now
# provided by the conftest.py file.


def test_collect_tweets_success(client, db_session, mock_twitter_client):
    """Test the /tweets/collect endpoint with valid data."""
    mock_twitter_client.search_recent.return_value = {
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
    assert "id" in data[0]
    assert data[0]["tweet_id"] == "1"
    assert data[1]["tweet_id"] == "2"

def test_collect_tweets_empty_query(client):
    """Test the /tweets/collect endpoint with an empty query."""
    response = client.post("/tweets/collect", json={"query": ""})
    assert response.status_code == 422
    assert "query" in response.json()["detail"][0]["loc"]

def test_collect_tweets_api_error(client, mock_twitter_client):
    """Test API endpoint when Twitter API returns an error."""
    mock_twitter_client.search_recent.side_effect = TwitterAPIError("Simulated API error")
    response = client.post("/tweets/collect", json={"query": "error"})
    assert response.status_code == 502
    assert "Twitter API error" in response.json()["detail"]

def test_list_tweets_success(client, db_session):
    """Test the /tweets endpoint with stored tweets."""
    db_session.add(Tweet(tweet_id="100", text="Test tweet 1", created_at="2025-01-01T10:00:00Z"))
    db_session.add(Tweet(tweet_id="101", text="Test tweet 2", created_at="2025-01-01T11:00:00Z"))
    db_session.commit()
    
    response = client.get("/tweets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "101"

def test_list_tweets_limit(client, db_session):
    """Test the limit parameter on /tweets."""
    db_session.add(Tweet(tweet_id="102", text="Tweet 1"))
    db_session.add(Tweet(tweet_id="103", text="Tweet 2"))
    db_session.add(Tweet(tweet_id="104", text="Tweet 3"))
    db_session.commit()
    
    response = client.get("/tweets/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["tweet_id"] == "104"
    assert data[1]["tweet_id"] == "103"


def test_list_tweets_database_empty(client):
    """Test the /tweets endpoint when the database is empty."""
    response = client.get("/tweets/")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_get_top_hashtags_success(client, db_session):
    """Test the /analytics/hashtags endpoint with valid data."""
    db_session.add(Tweet(text="A tweet with #PyTest and #FastAPI."))
    db_session.add(Tweet(text="Another tweet with #FastAPI."))
    db_session.add(Tweet(text="A third tweet with no hashtags."))
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
    """Test /analytics/hashtags with an empty database."""
    response = client.get("/analytics/hashtags")
    assert response.status_code == 200
    assert response.json()["top_hashtags"] == []

def test_get_volume_by_hour_success(client, db_session):
    """Test the /analytics/volume_by_hour endpoint."""
    db_session.add(Tweet(created_at="2025-01-01T10:00:00.000Z"))
    db_session.add(Tweet(created_at="2025-01-01T10:30:00.000Z"))
    db_session.add(Tweet(created_at="2025-01-01T11:00:00.000Z"))
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
    """Test /analytics/volume_by_hour with an empty database."""
    response = client.get("/analytics/volume_by_hour")
    assert response.status_code == 200
    assert response.json()["volume_by_hour"] == []

# --- Load Test (Simple) ---

def test_simple_load_test(client, mock_twitter_client):
    """Simulates inserting 1000 tweets rapidly."""
    total_tweets = 1000
    mock_data = {
        "data": [
            {
                "id": f"load_test_{i}",
                "text": f"Load test tweet #{i}",
                "author_id": "load_user",
                "created_at": "2025-01-01T12:00:00.000Z"
            } for i in range(100)
        ],
        "meta": {"result_count": 100}
    }
    
    mock_twitter_client.search_recent.return_value = mock_data
    
    response = client.post("/tweets/collect", json={"query": "load_test", "max_results": 100})
    
    assert response.status_code == 200
    assert len(response.json()) == 100
    
    response = client.get("/tweets/", params={"limit": 1000})
    assert response.status_code == 200
    assert len(response.json()) > 0