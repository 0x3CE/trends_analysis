# app/tests/test_models.py
"""Tests for database models."""
import pytest
from datetime import datetime
from app.models import Tweet


def test_tweet_creation(db_session):
    """Test de création d'un tweet."""
    tweet = Tweet(
        tweet_id="123456789",
        author_id="user123",
        text="Test tweet content",
        created_at=datetime.now(),
        raw_json='{"test": "data"}'
    )
    
    db_session.add(tweet)
    db_session.commit()
    
    assert tweet.id is not None
    assert tweet.tweet_id == "123456789"
    assert tweet.author_id == "user123"


def test_tweet_unique_constraint(db_session):
    """Test de la contrainte d'unicité sur tweet_id."""
    from sqlalchemy.exc import IntegrityError
    
    # Premier tweet
    tweet1 = Tweet(tweet_id="123", text="First tweet")
    db_session.add(tweet1)
    db_session.commit()
    
    # Second tweet avec le même tweet_id
    tweet2 = Tweet(tweet_id="123", text="Duplicate tweet")
    db_session.add(tweet2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()