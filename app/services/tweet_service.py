# app/services/tweet_service.py (version améliorée)
"""Tweet collection and management service.

* **Rôle global** : C’est le **service métier qui gère les tweets** : collecte via l’API Twitter/X (via `twitter_client`), insertion en base, lecture, et comptage. C’est lui qui fait tout le boulot derrière `routes/tweets.py`.

* **Fonctionnalités** :

  1. **`collect_tweets(query, max_results, db)`**

     * Vérifie la validité des paramètres (`query` non vide, `max_results > 0`).
     * Appelle le client Twitter (`twitter_client.search_recent`).
     * Pour chaque tweet trouvé :

       * Appelle `_save_tweet_if_new()` pour vérifier et insérer.
       * Compte les succès/erreurs.
     * Retourne la liste des tweets insérés.
     * Gestion robuste : si erreur API → `TwitterAPIError`, si problème DB → rollback + `DatabaseError`.

  2. **`_save_tweet_if_new(tweet_data, db)` (privé)**

     * Vérifie que `tweet_data` est un dict valide et contient un `id`.
     * Check si le tweet existe déjà (`tweet_id`).
     * Parse la date de création avec `_parse_tweet_date`.
     * Construit un modèle `Tweet` et l’insère en DB.
     * Gère les erreurs :

       * **Doublon** → rollback + warning.
       * **Autre erreur DB** → rollback + log.

  3. **`_parse_tweet_date(date_str)` (privé)**

     * Parse une date Twitter (formats ISO8601 variés).
     * Supporte :

       * Format standard `YYYY-MM-DDTHH:MM:SSZ`.
       * Format avec timezone explicite (`+00:00`).
       * Fallback → ajoute `+00:00`.
     * Si parsing échoue → log warning et retourne `None`.

  4. **`get_tweets(limit, db)`**

     * Récupère les tweets en DB, triés par `created_at` desc.
     * Limite entre 1 et 1000 (au-delà → warning sur pagination).
     * Retourne une liste de `Tweet`.

  5. **`get_tweets_count(db)`**

     * Retourne le nombre total de tweets en DB.
     * En cas d’erreur → `DatabaseError`.

* **Points forts** :

  * Gestion robuste des erreurs (rollback systématique si DB plante).
  * Vérifications strictes des entrées.
  * Journalisation détaillée (info, debug, warning, error).
  * Bonne séparation des responsabilités (collecte / sauvegarde / parsing / lecture).

👉 En résumé : ce fichier est le **moteur de persistance et de collecte des tweets**.
Là où `analytics_service` exploite les tweets déjà stockés, **`tweet_service` est celui qui les fait rentrer dans le système**.

Tu veux que je t’enchaîne le résumé du **`twitter_client`** quand tu me l’envoies ? Je sens que c’est la pièce qui ferme la boucle côté API externe 🔗.

"""
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
    """Service pour la gestion des tweets avec gestion d'erreurs robuste."""

    @staticmethod
    def collect_tweets(query: str, max_results: int, db: Session) -> List[models.Tweet]:
        """
        Collecte des tweets depuis l'API et les sauvegarde en base.
        Améliore la gestion d'erreurs et la validation des entrées.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace-only.")

        if max_results <= 0:
            raise ValueError("max_results must be greater than 0.")

        if not twitter_client:
            raise TwitterAPIError("Twitter client not configured. Check BEARER_TOKEN.")

        try:
            api_response = twitter_client.search_recent(query.strip(), max_results)
            tweets_data = api_response.get("data", [])

            if not tweets_data:
                logger.info(f"No tweets found for query: {query}")
                return []

            saved_tweets = []
            errors_count = 0
            
            for tweet_data in tweets_data:
                try:
                    tweet = TweetService._save_tweet_if_new(tweet_data, db)
                    if tweet:
                        saved_tweets.append(tweet)
                except Exception as e:
                    errors_count += 1
                    logger.error(f"Failed to save tweet {tweet_data.get('id', 'unknown')}: {e}")
                    continue

            logger.info(f"Successfully saved {len(saved_tweets)} new tweets, {errors_count} errors")
            return saved_tweets

        except TwitterAPIError as e:
            logger.error(f"Twitter API error during collection: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during tweet collection: {e}")
            db.rollback()
            raise DatabaseError(f"Tweet collection failed: {str(e)}")

    @staticmethod
    def _save_tweet_if_new(tweet_data: dict, db: Session) -> Optional[models.Tweet]:
        """
        Sauvegarde un tweet avec validation et gestion d'erreurs améliorée.
        """
        if not isinstance(tweet_data, dict):
            logger.warning("Invalid tweet data format: expected dict")
            return None
            
        tweet_id = tweet_data.get("id")
        if not tweet_id or not str(tweet_id).strip():
            logger.warning(f"Skipping tweet without valid id: {tweet_data}")
            return None

        try:
            # Vérification d'existence avec gestion d'erreurs
            existing = db.query(models.Tweet).filter(
                models.Tweet.tweet_id == str(tweet_id)
            ).first()
            
            if existing:
                logger.debug(f"Tweet {tweet_id} already exists, skipping")
                return None

        except Exception as e:
            logger.error(f"Error checking tweet existence for {tweet_id}: {e}")
            return None

        # Parsing de la date avec gestion d'erreurs robuste
        created_at = TweetService._parse_tweet_date(tweet_data.get("created_at"))

        new_tweet = models.Tweet(
            tweet_id=str(tweet_id),
            author_id=tweet_data.get("author_id"),
            text=tweet_data.get("text", ""),
            created_at=created_at,
            raw_json=json.dumps(tweet_data, ensure_ascii=False)
        )

        try:
            db.add(new_tweet)
            db.commit()
            db.refresh(new_tweet)
            logger.debug(f"Successfully saved tweet {tweet_id}")
            return new_tweet
            
        except IntegrityError as e:
            db.rollback()
            logger.warning(f"Tweet {tweet_id} already exists (integrity constraint): {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Database error saving tweet {tweet_id}: {e}")
            return None

    @staticmethod
    def _parse_tweet_date(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse la date du tweet avec gestion d'erreurs robuste.
        Supporte différents formats de date Twitter.
        """
        if not date_str:
            return None
            
        try:
            # Format Twitter standard ISO8601
            if date_str.endswith('Z'):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif '+' in date_str or date_str.endswith('+00:00'):
                return datetime.fromisoformat(date_str)
            else:
                # Fallback pour d'autres formats
                return datetime.fromisoformat(date_str + "+00:00")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format '{date_str}': {e}")
            return None

    @staticmethod
    def get_tweets(limit: int, db: Session) -> List[models.Tweet]:
        """
        Récupère les tweets avec validation des paramètres et gestion d'erreurs.
        """
        if limit <= 0:
            raise ValueError("Limit must be greater than 0")
            
        if limit > 1000:
            logger.warning(f"Large limit requested: {limit}, consider pagination")
            
        try:
            return db.query(models.Tweet)\
                     .order_by(models.Tweet.created_at.desc())\
                     .limit(limit)\
                     .all()
        except Exception as e:
            logger.error(f"Database error retrieving tweets: {e}")
            raise DatabaseError(f"Failed to retrieve tweets: {str(e)}")

    @staticmethod
    def get_tweets_count(db: Session) -> int:
        """Retourne le nombre total de tweets en base."""
        try:
            return db.query(models.Tweet).count()
        except Exception as e:
            logger.error(f"Error counting tweets: {e}")
            raise DatabaseError(f"Failed to count tweets: {str(e)}")