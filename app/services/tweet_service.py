# app/services/tweet_service.py
"""Tweet collection and management service."""
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models, schemas
from ..exceptions import DatabaseError
from .twitter_client import twitter_client

logger = logging.getLogger(__name__)


class TweetService:
    """Service pour la gestion des tweets (collecte, stockage, récupération)."""
    
    @staticmethod
    def collect_tweets(
        query: str, 
        max_results: int, 
        db: Session
    ) -> List[models.Tweet]:
        """
        Collecte des tweets depuis l'API et les sauvegarde en base.
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de tweets à collecter
            db: Session de base de données
        
        Returns:
            List[models.Tweet]: Liste des nouveaux tweets sauvegardés
        
        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        if not twitter_client:
            raise ValueError("Twitter client not configured. Check BEARER_TOKEN.")
        
        try:
            # Appel à l'API Twitter
            api_response = twitter_client.search_recent(query, max_results)
            tweets_data = api_response.get("data", [])
            
            if not tweets_data:
                logger.info("No tweets found for the given query")
                return []
            
            saved_tweets = []
            
            for tweet_data in tweets_data:
                try:
                    saved_tweet = TweetService._save_tweet_if_new(tweet_data, db)
                    if saved_tweet:
                        saved_tweets.append(saved_tweet)
                except Exception as e:
                    logger.error(f"Failed to save tweet {tweet_data.get('id')}: {e}")
                    continue
            
            logger.info(f"Successfully saved {len(saved_tweets)} new tweets")
            return saved_tweets
            
        except Exception as e:
            logger.error(f"Failed to collect tweets: {e}")
            db.rollback()
            raise DatabaseError(f"Tweet collection failed: {str(e)}")
    
    @staticmethod
    def _save_tweet_if_new(tweet_data: dict, db: Session) -> Optional[models.Tweet]:
        """
        Sauvegarde un tweet s'il n'existe pas déjà en base.
        
        Args:
            tweet_data: Données du tweet depuis l'API
            db: Session de base de données
        
        Returns:
            models.Tweet: Tweet sauvegardé ou None si déjà existant
        """
        tweet_id = tweet_data.get("id")
        if not tweet_id:
            return None
        
        # Vérification d'existence
        existing_tweet = db.query(models.Tweet).filter(
            models.Tweet.tweet_id == tweet_id
        ).first()
        
        if existing_tweet:
            logger.debug(f"Tweet {tweet_id} already exists, skipping")
            return None
        
        try:
            # Création du nouveau tweet
            new_tweet = models.Tweet(
                tweet_id=tweet_id,
                author_id=tweet_data.get("author_id"),
                text=tweet_data.get("text", ""),
                created_at=tweet_data.get("created_at"),
                raw_json=json.dumps(tweet_data, ensure_ascii=False)
            )
            
            db.add(new_tweet)
            db.commit()
            db.refresh(new_tweet)
            
            logger.debug(f"Successfully saved tweet {tweet_id}")
            return new_tweet
            
        except IntegrityError as e:
            logger.warning(f"Tweet {tweet_id} already exists (integrity constraint)")
            db.rollback()
            return None
    
    @staticmethod
    def get_tweets(limit: int, db: Session) -> List[models.Tweet]:
        """
        Récupère les tweets les plus récents.
        
        Args:
            limit: Nombre maximum de tweets à récupérer
            db: Session de base de données
        
        Returns:
            List[models.Tweet]: Liste des tweets triés par date décroissante
        """
        try:
            return (
                db.query(models.Tweet)
                .order_by(models.Tweet.created_at.desc())
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to retrieve tweets: {e}")
            raise DatabaseError(f"Failed to retrieve tweets: {str(e)}")
