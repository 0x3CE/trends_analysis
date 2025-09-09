# app/tests/test_routes.py
"""Tests for API routes."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestTweetsRoutes:
    """Tests pour les routes de tweets."""
    
    @patch('app.routes.tweets.TweetService.collect_tweets')
    def test_collect_tweets_endpoint(self, mock_collect, client):
        """Test de l'endpoint de collecte de tweets."""
        from app.models import Tweet
        
        # Configuration du mock
        mock_tweet = Tweet(
            id=1,
            tweet_id="123456789",
            text="Test tweet",
            author_id="user123"
        )
        mock_collect.return_value = [mock_tweet]
        
        # Requête
        response = client.post(
            "/tweets/collect",
            json={"query": "python", "max_results": 10}
        )
        
        # Vérifications
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tweet_id"] == "123456789"
        assert data[0]["text"] == "Test tweet"
    
    def test_collect_tweets_validation_error(self, client):
        """Test de validation des paramètres d'entrée."""
        # Requête avec paramètres invalides
        response = client.post(
            "/tweets/collect",
            json={"query": "", "max_results": 200}  # Query vide, max_results trop grand
        )
        
        # Vérifications
        assert response.status_code == 422  # Validation Error
    
    @patch('app.routes.tweets.TweetService.get_tweets')
    def test_list_tweets_endpoint(self, mock_get_tweets, client):
        """Test de l'endpoint de liste des tweets."""
        from app.models import Tweet
        
        # Configuration du mock
        mock_tweets = [
            Tweet(id=1, tweet_id="1", text="Tweet 1"),
            Tweet(id=2, tweet_id="2", text="Tweet 2"),
        ]
        mock_get_tweets.return_value = mock_tweets
        
        # Requête
        response = client.get("/tweets/?limit=10")
        
        # Vérifications
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["tweet_id"] == "1"
        assert data[1]["tweet_id"] == "2"


class TestAnalyticsRoutes:
    """Tests pour les routes d'analytics."""
    
    @patch('app.routes.analytics.AnalyticsService.get_top_hashtags')
    def test_hashtags_endpoint(self, mock_hashtags, client):
        """Test de l'endpoint d'analyse des hashtags."""
        # Configuration du mock
        mock_hashtags.return_value = [
            {"hashtag": "#python", "count": 5},
            {"hashtag": "#fastapi", "count": 3},
        ]
        
        # Requête
        response = client.get("/analytics/hashtags?limit=10")
        
        # Vérifications
        assert response.status_code == 200
        data = response.json()
        assert "top_hashtags" in data
        assert len(data["top_hashtags"]) == 2
        assert data["top_hashtags"][0]["hashtag"] == "#python"
        assert data["top_hashtags"][0]["count"] == 5
    
    def test_sentiment_endpoint_not_implemented(self, client):
        """Test de l'endpoint de sentiment (non implémenté)."""
        response = client.get("/analytics/sentiment")
        
        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()