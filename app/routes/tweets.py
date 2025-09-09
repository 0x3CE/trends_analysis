# app/routes/tweets.py
"""Tweet collection and retrieval endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from .. import schemas
from ..database import get_db
from ..services.tweet_service import TweetService
from ..exceptions import TwitterAPIError, DatabaseError

from ..utils import analyse_hashtag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tweets", tags=["tweets"])


@router.post("/collect", response_model=List[schemas.TweetRead])
async def collect_tweets(
    payload: schemas.CollectRequest, 
    db: Session = Depends(get_db)
) -> List[schemas.TweetRead]:
    """
    Collecte des tweets depuis l'API Twitter/X et les stocke en base.
    
    Args:
        payload: Requête contenant la query et le nombre max de résultats
        db: Session de base de données injectée
    
    Returns:
        List[schemas.TweetRead]: Liste des nouveaux tweets collectés
    
    Raises:
        HTTPException: 502 pour erreurs API, 500 pour erreurs internes
    """
    try:
        logger.info(f"Starting tweet collection for query: {payload.query}")
        
        saved_tweets = TweetService.collect_tweets(
            query=payload.query,
            max_results=payload.max_results,
            db=db
        )
        
        # Conversion vers le schema de réponse
        result = [schemas.TweetRead.from_orm(tweet) for tweet in saved_tweets]
        
        logger.info(f"Successfully collected {len(result)} tweets")
        return result
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error during collection: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error calling Twitter/X API: {str(e)}"
        )
    except DatabaseError as e:
        logger.error(f"Database error during collection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during tweet collection: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during tweet collection"
        )


@router.get("/", response_model=List[schemas.TweetRead])
async def list_tweets(
    limit: int = 50, 
    db: Session = Depends(get_db)
) -> List[schemas.TweetRead]:
    """
    Récupère la liste des tweets stockés, triés par date décroissante.
    
    Args:
        limit: Nombre maximum de tweets à retourner (défaut: 50)
        db: Session de base de données injectée
    
    Returns:
        List[schemas.TweetRead]: Liste des tweets
    """
    try:
        # Validation du paramètre limit
        limit = max(1, min(1000, limit))  # Entre 1 et 1000
        
        tweets = TweetService.get_tweets(limit=limit, db=db)
        result = [schemas.TweetRead.from_orm(tweet) for tweet in tweets]
        
        logger.info(f"Retrieved {len(result)} tweets")
        return result
        
    except DatabaseError as e:
        logger.error(f"Database error during tweet retrieval: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during tweet retrieval: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during tweet retrieval"
        )


@router.get("/top-hashtags")
def get_top_hashtags(tweets: list[str]):
    return analyse_hashtag.top_hashtags(tweets)