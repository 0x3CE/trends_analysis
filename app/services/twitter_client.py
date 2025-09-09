# app/services/twitter_client.py
"""Twitter/X API client service."""
import requests
import logging
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import settings
from ..exceptions import TwitterAPIError, ConfigurationError

logger = logging.getLogger(__name__)


class TwitterClient:
    """
    Client pour l'API Twitter/X v2 avec gestion d'erreurs robuste et retry automatique.
    """
    
    def __init__(self):
        """Initialise le client avec la configuration et les headers d'authentification."""
        if not settings.bearer_token:
            raise ConfigurationError("BEARER_TOKEN environment variable is required")
        
        self.base_url = settings.x_api_base
        self.headers = {"Authorization": f"Bearer {settings.bearer_token}"}
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Crée une session HTTP avec retry automatique et timeout configuré.
        
        Returns:
            requests.Session: Session configurée avec retry policy
        """
        session = requests.Session()
        session.headers.update(self.headers)
        
        # Stratégie de retry pour la robustesse
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        return session
    
    def search_recent(
        self, 
        query: str, 
        max_results: int = 10, 
        next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Effectue une recherche de tweets récents via l'API Twitter/X v2.
        
        Args:
            query: Requête de recherche (mots-clés, hashtags, etc.)
            max_results: Nombre de résultats souhaités (10-100)
            next_token: Token pour la pagination (optionnel)
        
        Returns:
            Dict: Réponse JSON de l'API
        
        Raises:
            TwitterAPIError: En cas d'erreur API
        """
        url = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max(10, min(100, max_results)),
            "tweet.fields": "created_at,author_id,text,id"
        }
        
        if next_token:
            params["next_token"] = next_token
        
        try:
            logger.info(f"Searching tweets with query: {query}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully retrieved {len(data.get('data', []))} tweets")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Twitter API request failed: {e}")
            raise TwitterAPIError(f"Failed to fetch tweets from Twitter API: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid JSON response from Twitter API: {e}")
            raise TwitterAPIError(f"Invalid response from Twitter API: {str(e)}")


# Instance globale du client Twitter
twitter_client = TwitterClient() if settings.bearer_token else None
