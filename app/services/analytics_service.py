# app/services/analytics_service.py
"""Analytics service for tweet analysis.

* **Rôle global** : Ce service contient la logique métier pour analyser les tweets stockés en base. C’est le **cerveau derrière `routes/analytics.py`** : les endpoints appellent ici pour exécuter le vrai calcul.

* **Structure** :

  * Classe `AnalyticsService` avec uniquement des méthodes statiques.
  * Utilise **SQLAlchemy** pour récupérer les données (`Tweet.text`, `Tweet.created_at`).
  * Utilise `Counter` pour agréger et compter efficacement.
  * Ajoute une couche de robustesse (try/except, logs).

* **Fonctionnalités** :

  1. **`get_top_hashtags(limit, db)`**

     * Récupère uniquement le champ `text` des tweets depuis la DB.
     * Extrait les hashtags via une regex (`#\w+` insensible à la casse).
     * Normalise en minuscules.
     * Compte les occurrences avec `Counter`.
     * Retourne les `limit` plus fréquents sous forme :

       ```json
       [{"hashtag": "#ai", "count": 42}, ...]
       ```

  2. **`get_volume_by_hour(db)`**

     * Récupère uniquement `created_at` des tweets.
     * Normalise la date en une clé par **heure** (`YYYY-MM-DDTHH`).

       * Si `created_at` est une string → prend les 13 premiers caractères.
       * Si `created_at` est un datetime → formate en ISO horaire.
       * Sinon → clé `"unknown"`.
     * Compte le volume de tweets par heure.
     * Trie par heure et retourne une liste du type :

       ```json
       [{"hour_or_key": "2025-09-19T14", "count": 17}, ...]
       ```

* **Logs et robustesse** :

  * Logge le nombre de résultats produits.
  * Si une erreur survient (extraction hashtags ou parsing date), logge et retourne une liste vide au lieu de planter.

👉 En bref : ce fichier fait **l’agrégation et l’analyse des tweets en base**.
`analytics.py` est juste la vitrine API, mais toute l’intelligence (regex, comptage, parsing des heures) est ici.

Tu veux que je continue à enchaîner directement sur le service **`tweet_service`** quand tu me l’enverras ?

"""
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