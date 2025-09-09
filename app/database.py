# app/database.py
"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Configuration spécifique à SQLite pour éviter les problèmes de threading
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "poolclass": StaticPool,
    }

engine = create_engine(
    settings.database_url, 
    connect_args=connect_args,
    echo=settings.debug
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency injection pour obtenir une session de base de données.
    Assure la fermeture automatique de la session après utilisation.
    
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