# tests/test_unit_services.py
import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models import Tweet
from app.services.tweet_service import TweetService
from app.services.analytics_service import AnalyticsService
from app.exceptions import DatabaseError, TwitterAPIError

# --- Unit Tests for TweetService ---

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_twitter_client():
    """Mocks the Twitter client."""
    with patch('app.services.tweet_service.twitter_client') as mock_client:
        yield mock_client

def test_collect_tweets_success(mock_db_session, mock_twitter_client):
    """Test successful tweet collection and saving."""
    mock_twitter_client.search_recent.return_value = {
        "data": [
            {"id": "1", "text": "Hello #Python", "author_id": "user1"},
            {"id": "2", "text": "FastAPI is great", "author_id": "user2"}
        ]
    }
    
    # Simulate a new tweet
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    tweets = TweetService.collect_tweets("test", 10, mock_db_session)
    
    assert len(tweets) == 2
    assert tweets[0].tweet_id == "1"
    assert "Python" in tweets[0].text
    
    assert mock_db_session.add.call_count == 2
    assert mock_db_session.commit.call_count == 2
    assert mock_db_session.refresh.call_count == 2

def test_collect_tweets_no_data(mock_db_session, mock_twitter_client):
    """Test collection when API returns no tweets."""
    mock_twitter_client.search_recent.return_value = {"data": []}
    
    tweets = TweetService.collect_tweets("empty", 10, mock_db_session)
    
    assert len(tweets) == 0
    mock_db_session.add.assert_not_called()

def test_collect_tweets_duplicate(mock_db_session, mock_twitter_client):
    """Test handling of duplicate tweets."""
    mock_twitter_client.search_recent.return_value = {
        "data": [
            {"id": "1", "text": "Existing tweet"},
            {"id": "2", "text": "New tweet"}
        ]
    }
    
    # Simulate first tweet exists, second is new
    existing_tweet = Tweet(tweet_id="1", text="Existing tweet")
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        existing_tweet,  # For the first tweet
        None             # For the second tweet
    ]
    
    tweets = TweetService.collect_tweets("test", 10, mock_db_session)
    
    assert len(tweets) == 1
    assert tweets[0].tweet_id == "2"
    
    assert mock_db_session.add.call_count == 1
    assert mock_db_session.commit.call_count == 1

def test_collect_tweets_api_limit_reached(mock_db_session, mock_twitter_client):
    """Test handling of API limit error."""
    mock_twitter_client.search_recent.side_effect = TwitterAPIError("Rate limit exceeded")
    
    with pytest.raises(DatabaseError, match="Tweet collection failed"):
        TweetService.collect_tweets("limit", 10, mock_db_session)

def test_get_tweets_success(mock_db_session):
    """Test successful tweet retrieval."""
    mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
        Tweet(id=1, tweet_id="1", text="Tweet 1"),
        Tweet(id=2, tweet_id="2", text="Tweet 2")
    ]
    
    tweets = TweetService.get_tweets(10, mock_db_session)
    
    assert len(tweets) == 2
    assert tweets[0].tweet_id == "1"

def test_get_tweets_database_empty(mock_db_session):
    """Test retrieval from an empty database."""
    mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
    
    tweets = TweetService.get_tweets(10, mock_db_session)
    
    assert len(tweets) == 0

# --- Unit Tests for AnalyticsService ---

@pytest.fixture
def sample_tweets():
    """Provides sample Tweet objects for analytics tests."""
    return [
        Tweet(text="A test tweet with #PyTest and #FastAPI."),
        Tweet(text="Another test with #FastAPI and #Docker."),
        Tweet(text="A third tweet with no hashtags."),
        Tweet(text="A tweet with #pytest, just for case testing.")
    ]

def test_get_top_hashtags_success(mock_db_session, sample_tweets):
    """Test successful hashtag analysis."""
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        (t.text,) for t in sample_tweets
    ]
    
    hashtags = AnalyticsService.get_top_hashtags(10, mock_db_session)
    
    assert len(hashtags) == 4
    assert hashtags[0]["hashtag"] == "#fastapi"
    assert hashtags[0]["count"] == 2
    assert hashtags[1]["hashtag"] == "#pytest"
    assert hashtags[1]["count"] == 2
    assert hashtags[2]["hashtag"] == "#docker"
    assert hashtags[2]["count"] == 1
    assert hashtags[3]["hashtag"] == "#pytest"
    assert hashtags[3]["count"] == 2

def test_get_top_hashtags_empty_db(mock_db_session):
    """Test hashtag analysis with an empty database."""
    mock_db_session.query.return_value.filter.return_value.all.return_value = []
    
    hashtags = AnalyticsService.get_top_hashtags(10, mock_db_session)
    
    assert len(hashtags) == 0

def test_get_volume_by_hour_success(mock_db_session):
    """Test successful volume analysis."""
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        (datetime(2025, 1, 1, 10, 0, 0),),
        (datetime(2025, 1, 1, 10, 30, 0),),
        (datetime(2025, 1, 1, 11, 0, 0),)
    ]
    
    volume = AnalyticsService.get_volume_by_hour(mock_db_session)
    
    assert len(volume) == 2
    assert volume[0]["hour_or_key"] == "2025-01-01T10"
    assert volume[0]["count"] == 2
    assert volume[1]["hour_or_key"] == "2025-01-01T11"
    assert volume[1]["count"] == 1

def test_get_volume_by_hour_empty_db(mock_db_session):
    """Test volume analysis with an empty database."""
    mock_db_session.query.return_value.filter.return_value.all.return_value = []
    
    volume = AnalyticsService.get_volume_by_hour(mock_db_session)
    
    assert len(volume) == 0