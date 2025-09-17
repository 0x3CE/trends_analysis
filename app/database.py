# app/database.py
"""Database configuration and session management."""
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