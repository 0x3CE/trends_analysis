# app/routes/analytics.py
"""Analytics endpoints for tweet analysis.

* **Rôle global** : C’est un module FastAPI qui expose des endpoints REST pour faire des analyses sur les tweets (hashtags, volume horaire, et bientôt sentiment).

* **Structure** :

  * Il définit un **router FastAPI** avec le préfixe `/analytics`.
  * Il utilise `Depends(get_db)` pour injecter une session SQLAlchemy dans chaque endpoint.
  * Il délègue toute la logique métier à `AnalyticsService` (donc ce fichier n’analyse rien lui-même, il ne fait que router).

* **Endpoints** :

  1. **`/analytics/hashtags`**

     * Retourne les hashtags les plus populaires.
     * Paramètre `limit` (entre 1 et 100, défaut 20).
     * Retourne un dict : `{ "top_hashtags": [...] }`.

  2. **`/analytics/volume_by_hour`**

     * Retourne le nombre de tweets par heure.
     * Résultat : `{ "volume_by_hour": [...] }`.

  3. **`/analytics/sentiment`**

     * Pas encore implémenté.
     * Retourne un **501 Not Implemented** avec une note sur l’usage futur de bibliothèques NLP (TextBlob, VADER, Transformers).

* **Logs et erreurs** :

  * Chaque endpoint logge ce qu’il génère.
  * Si ça plante, ça remonte un **500 Internal Server Error** clair.

👉 Bref : ce fichier sert uniquement de **pont entre l’API (FastAPI) et la logique métier (AnalyticsService)**.

Tu veux m’envoyer le fichier **`analytics_service`** juste après ? Ce sera la pièce maîtresse derrière ces endpoints 🔑

"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..database import get_db
from ..services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/hashtags", response_model=Dict[str, Any])
async def get_top_hashtags(
    limit: int = 20, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyse et retourne les hashtags les plus populaires.
    
    Args:
        limit: Nombre maximum de hashtags à retourner (défaut: 20)
        db: Session de base de données injectée
    
    Returns:
        Dict: Dictionnaire contenant les top hashtags avec leurs compteurs
    """
    try:
        # Validation et normalisation du paramètre
        limit = max(1, min(100, limit))  # Entre 1 et 100
        
        top_hashtags = AnalyticsService.get_top_hashtags(limit=limit, db=db)
        
        logger.info(f"Generated hashtag analysis with {len(top_hashtags)} results")
        return {"top_hashtags": top_hashtags}
        
    except Exception as e:
        logger.error(f"Error during hashtag analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during hashtag analysis"
        )


@router.get("/volume_by_hour", response_model=Dict[str, Any])
async def get_volume_by_hour(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Analyse le volume de tweets par heure.
    
    Args:
        db: Session de base de données injectée
    
    Returns:
        Dict: Volume de tweets groupé par heure
    """
    try:
        volume_data = AnalyticsService.get_volume_by_hour(db=db)
        
        logger.info(f"Generated volume analysis with {len(volume_data)} time periods")
        return {"volume_by_hour": volume_data}
        
    except Exception as e:
        logger.error(f"Error during volume analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during volume analysis"
        )


@router.get("/sentiment")
async def get_sentiment_analysis():
    """
    Endpoint placeholder pour l'analyse de sentiment.
    À implémenter avec une bibliothèque de NLP (ex: TextBlob, VADER, transformers).
    """
    raise HTTPException(
        status_code=501,
        detail="Sentiment analysis endpoint not implemented yet. "
               "Consider integrating TextBlob, VADER, or Transformers library."
    )