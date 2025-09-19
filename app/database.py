# app/database.py
"""Database configuration and session management.

* **Rôle global** : gérer la **connexion à la base de données** et fournir une session SQLAlchemy utilisable via FastAPI.
  👉 C’est la colonne vertébrale de la persistance, utilisée par tous les services et routes.

* **Fonctionnalités principales** :

  1. **`create_database_engine()`**

     * Construit un moteur SQLAlchemy à partir de `settings.database_url`.
     * Si c’est **SQLite** → applique des configs spéciales :

       * `check_same_thread=False` (multi-threads autorisés).
       * `StaticPool` (utile pour tests et bases en mémoire).
     * Active le mode debug SQL (`echo=True`) si `settings.debug=True`.

  2. **Moteur et session**

     * `engine` → moteur DB global.
     * `SessionLocal` → factory de sessions (`autocommit=False`, `autoflush=False`).
     * `Base = declarative_base()` → base des modèles ORM (`models.Tweet`, etc.).

  3. **`get_db()`**

     * Fonction génératrice pour FastAPI (dépendance `Depends(get_db)`).
     * Fournit une session `db`.
     * Gère les erreurs : rollback en cas d’exception.
     * Ferme proprement la session dans tous les cas.

* **Intégration** :

  * Appelé dans les routes (`tweets.py`, `analytics.py`) via `Depends(get_db)`.
  * C’est le lien entre les **routes/services** et la base physique (SQLite, Postgres, etc.).

👉 En résumé : ce fichier est le **plomberie DB** de l’app : création moteur, session, injection dans FastAPI, avec robustesse et compatibilité SQLite.

Tu veux que je passe aux **models** (vu qu’ils héritent de `Base`) pour compléter le puzzle ORM ?

"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)


def create_database_engine():
    """Crée et configure le moteur de base de données selon l'environnement."""
    engine_kwargs = {"echo": settings.debug}
    
    # Configuration spécifique pour SQLite
    if settings.database_url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool
        })
    
    return create_engine(settings.database_url, **engine_kwargs)


# Initialisation du moteur et de la session
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency injection pour obtenir une session de base de données.
    Gère automatiquement l'ouverture, les erreurs et la fermeture de session.
    
    Yields:
        Session: Session SQLAlchemy configurée
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()