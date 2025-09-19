# app/main.py
"""Main FastAPI application setup and configuration.


### 🎯 Objectif principal

* Configurer et lancer l’API FastAPI.
* Gérer le cycle de vie (lifespan), la sécurité (middlewares), les exceptions globales, et exposer les routes.

---

### ⚙️ Les parties essentielles

1. **Configuration du logging**

   * Log formaté et niveau `INFO` par défaut.
   * Permet un suivi clair du démarrage, de l’arrêt et des erreurs.

2. **`lifespan(app)` (asynccontextmanager)**

   * Démarrage :

     * Log “starting”.
     * Création des tables DB (`Base.metadata.create_all(bind=engine)`).
     * Vérifie que le `BEARER_TOKEN` est bien configuré (sinon warning).
   * Arrêt :

     * Log “shutting down”.
       👉 C’est ici que tu initialises tes dépendances critiques.

3. **Instance FastAPI (`app = FastAPI(...)`)**

   * Titre = `settings.app_name`.
   * Docs & Redoc activés uniquement si `debug=True`.
   * Version figée à `1.0.0`.

4. **Middleware**

   * `TrustedHostMiddleware` :

     * `*` si debug, sinon restreint à `localhost`.
   * `CORS` (Cross-Origin Resource Sharing) :

     * Ouvert à tous (`*`) si debug (utile en dev front/back séparés).

5. **Gestion des exceptions globales**

   * `TwitterAPIError` → `502 Bad Gateway`.
   * `DatabaseError` → `500 Internal Server Error`.
   * `ConfigurationError` → `500 Internal Server Error`.
     👉 Ces handlers renvoient toujours une réponse JSON uniforme (`{"detail": ...}`).

6. **Inclusion des routeurs**

   * `tweets.router` → endpoints liés à la collecte/lecture des tweets.
   * `analytics.router` → endpoints pour analyser les données (hashtags, stats).

7. **Endpoints de santé (`/` et `/health`)**

   * `/` → health check basique (status, nom app, version, API configurée ou non).
   * `/health` → health check détaillé :

     * Vérifie DB avec `SELECT 1`.
     * Vérifie présence de `BEARER_TOKEN`.
     * Retourne un statut global (`healthy` ou `degraded`).

---

### 🚀 En clair

Ce fichier **démarre ton app**, **branche la DB**, **sécurise les accès**, et **prépare les routes**.
Il agit comme le **point d’entrée unique** et garantit que tout est prêt avant que les requêtes arrivent.

---

👉 Tu veux que je trace maintenant la **vision complète du flow de données** (depuis un appel API → DB → retour API), histoire de voir comment tout s’imbrique ?

"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import engine, Base
from .routes import tweets, analytics
from .exceptions import TwitterAPIError, DatabaseError, ConfigurationError

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire du cycle de vie de l'application.
    Initialise la base de données au démarrage.
    """
    try:
        logger.info("Starting Twitter/X Collector application")
        
        # Création des tables de base de données
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Vérification de la configuration
        if not settings.bearer_token:
            logger.warning("BEARER_TOKEN not configured - API calls will fail")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        logger.info("Shutting down Twitter/X Collector application")


# Création de l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API pour collecter et analyser des tweets depuis l'API Twitter/X v2",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Middleware de sécurité
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Middleware CORS pour le développement
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Gestionnaires d'exceptions globaux
@app.exception_handler(TwitterAPIError)
async def twitter_api_exception_handler(request: Request, exc: TwitterAPIError):
    """Gestionnaire pour les erreurs de l'API Twitter."""
    logger.error(f"Twitter API error: {exc}")
    return JSONResponse(
        status_code=502,
        content={"detail": f"Twitter API error: {str(exc)}"}
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Gestionnaire pour les erreurs de base de données."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {str(exc)}"}
    )


@app.exception_handler(ConfigurationError)
async def configuration_exception_handler(request: Request, exc: ConfigurationError):
    """Gestionnaire pour les erreurs de configuration."""
    logger.error(f"Configuration error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Configuration error: {str(exc)}"}
    )


# Inclusion des routeurs
app.include_router(tweets.router)
app.include_router(analytics.router)


@app.get("/", tags=["health"])
async def health_check():
    """
    Endpoint de santé de l'application.
    
    Returns:
        Dict: Statut de l'application et informations système
    """
    return {
        "status": "healthy",
        "message": f"{settings.app_name} is running",
        "version": "1.0.0",
        "api_configured": settings.bearer_token is not None
    }


@app.get("/health", tags=["health"])
async def detailed_health_check():
    """
    Endpoint de santé détaillé avec vérification des dépendances.
    
    Returns:
        Dict: Statut détaillé de l'application
    """
    health_status = {
        "status": "healthy",
        "checks": {
            "database": "ok",
            "twitter_api": "configured" if settings.bearer_token else "not_configured"
        },
        "timestamp": "2025-01-09T00:00:00Z"
    }
    
    try:
        # Test simple de la base de données
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    return health_status