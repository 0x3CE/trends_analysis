# app/services/analytics_service.py
"""Analytics service for tweet analysis."""
import re
import logging
from typing import Dict, List, Tuple
from collections import Counter
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service pour l'analyse des tweets (hashtags, volume, etc.)."""
    
    # Pattern regex optimisé pour les hashtags
    HASHTAG_PATTERN = re.compile(r"#\w+", re.IGNORECASE)
    
    @staticmethod
    def get_top_hashtags(limit: int, db: Session) -> List[Dict[str, any]]:
        """
        Analyse les hashtags les plus populaires dans les tweets stockés.
        
        Args:
            limit: Nombre maximum de hashtags à retourner
            db: Session de base de données
        
        Returns:
            List[Dict]: Liste des hashtags avec leur nombre d'occurrences
        """
        try:
            # Récupération efficace des textes uniquement
            tweet_texts = db.query(models.Tweet.text).filter(
                models.Tweet.text.isnot(None)
            ).all()
            
            if not tweet_texts:
                return []
            
            # Extraction et comptage des hashtags
            hashtag_counter = Counter()
            
            for (text,) in tweet_texts:
                hashtags = AnalyticsService.HASHTAG_PATTERN.findall(text)
                # Normalisation en minuscules
                normalized_hashtags = [tag.lower() for tag in hashtags]
                hashtag_counter.update(normalized_hashtags)
            
            # Tri et limitation des résultats
            top_hashtags = hashtag_counter.most_common(limit)
            
            result = [
                {"hashtag": hashtag, "count": count}
                for hashtag, count in top_hashtags
            ]
            
            logger.info(f"Found {len(result)} top hashtags")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze hashtags: {e}")
            return []
    
    @staticmethod
    def get_volume_by_hour(db: Session) -> List[Dict[str, any]]:
        """
        Analyse le volume de tweets par heure.
        
        Args:
            db: Session de base de données
        
        Returns:
            List[Dict]: Volume de tweets groupé par heure
        """
        try:
            # Récupération des dates de création
            tweet_dates = db.query(models.Tweet.created_at).filter(
                models.Tweet.created_at.isnot(None)
            ).all()
            
            if not tweet_dates:
                return []
            
            hour_counter = Counter()
            
            for (created_at,) in tweet_dates:
                if created_at:
                    try:
                        # Extraction de l'heure (format YYYY-MM-DD HH:00:00)
                        if isinstance(created_at, str):
                            # Si stocké comme string, prendre les 13 premiers caractères
                            hour_key = created_at[:13] if len(created_at) >= 13 else "unknown"
                        elif isinstance(created_at, datetime):
                            # Si datetime, formater proprement
                            hour_key = created_at.strftime("%Y-%m-%dT%H")
                        else:
                            hour_key = "unknown"
                            
                        hour_counter[hour_key] += 1
                        
                    except Exception as e:
                        logger.debug(f"Failed to parse date {created_at}: {e}")
                        hour_counter["unknown"] += 1
            
            # Tri par heure
            sorted_hours = sorted(hour_counter.items())
            
            result = [
                {"hour_or_key": hour, "count": count}
                for hour, count in sorted_hours
            ]
            
            logger.info(f"Analyzed volume for {len(result)} time periods")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze volume by hour: {e}")
            return []