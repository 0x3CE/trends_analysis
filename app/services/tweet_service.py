# app/services/tweet_service.py
"""Tweet collection and management service."""
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from .. import models
from ..exceptions import DatabaseError, TwitterAPIError
from .twitter_client import twitter_client

logger = logging.getLogger(__name__)


class TweetService:
    """Service pour la gestion des tweets (collecte, stockage, récupération)."""

    @staticmethod
    def collect_tweets(query: str, max_results: int, db: Session) -> List[models.Tweet]:
        """
        Collecte des tweets depuis l'API et les sauvegarde en base.
        """
        if not query:
            raise ValueError("Query cannot be empty.")

        if not twitter_client:
            raise ValueError("Twitter client not configured. Check BEARER_TOKEN.")

        try:
            api_response = twitter_client.search_recent(query, max_results)
            tweets_data = api_response.get("data", [])

            if not tweets_data:
                logger.info("No tweets found for the given query")
                return []

            saved_tweets = []
            for tweet_data in tweets_data:
                try:
                    tweet = TweetService._save_tweet_if_new(tweet_data, db)
                    if tweet:
                        saved_tweets.append(tweet)
                except Exception as e:
                    logger.error(f"Failed to save tweet {tweet_data.get('id')}: {e}")
                    continue

            logger.info(f"Successfully saved {len(saved_tweets)} new tweets")
            return saved_tweets

        except TwitterAPIError as e:
            logger.error(f"Twitter API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to collect tweets: {e}")
            db.rollback()
            raise DatabaseError(f"Tweet collection failed: {e}")

    @staticmethod
    def _save_tweet_if_new(tweet_data: dict, db: Session) -> Optional[models.Tweet]:
        """
        Sauvegarde un tweet s'il n'existe pas déjà en base.
        """
        tweet_id = tweet_data.get("id")
        if not tweet_id:
            logger.warning(f"Skipping tweet without id: {tweet_data}")
            return None

        existing = db.query(models.Tweet).filter(models.Tweet.tweet_id == tweet_id).first()
        if existing:
            return None

        created_at_str = tweet_data.get("created_at")
        created_at = None
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                logger.warning(f"Invalid created_at format for tweet {tweet_id}: {created_at_str}")

        new_tweet = models.Tweet(
            tweet_id=tweet_id,
            author_id=tweet_data.get("author_id"),
            text=tweet_data.get("text", ""),
            created_at=created_at,
            raw_json=json.dumps(tweet_data, ensure_ascii=False)
        )

        try:
            db.add(new_tweet)
            db.commit()
            db.refresh(new_tweet)
            return new_tweet
        except IntegrityError:
            db.rollback()
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save tweet {tweet_id}: {e}")
            return None

    @staticmethod
    def get_tweets(limit: int, db: Session) -> List[models.Tweet]:
        """
        Récupère les tweets les plus récents.
        """
        try:
            return db.query(models.Tweet)\
                     .order_by(models.Tweet.created_at.desc())\
                     .limit(limit)\
                     .all()
        except Exception as e:
            logger.error(f"Failed to retrieve tweets: {e}")
            raise DatabaseError(f"Failed to retrieve tweets: {e}")
