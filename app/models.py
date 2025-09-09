# app/models.py
"""Database models for the Twitter/X collector application."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.sql import func
from datetime import datetime

from .database import Base


class Tweet(Base):
    """
    Modèle de données pour stocker les tweets collectés.
    Optimisé avec des index pour les requêtes fréquentes.
    """
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tweet_id = Column(String(50), unique=True, nullable=False, comment="ID unique du tweet")
    author_id = Column(String(50), nullable=True, comment="ID de l'auteur du tweet")
    text = Column(Text, nullable=False, comment="Contenu textuel du tweet")
    created_at = Column(DateTime, nullable=True, comment="Date de création du tweet")
    collected_at = Column(DateTime, default=func.now(), nullable=False, comment="Date de collecte")
    raw_json = Column(Text, nullable=True, comment="JSON brut de l'API Twitter")
    
    # Index composé pour optimiser les requêtes par auteur et date
    __table_args__ = (
        Index('ix_tweet_author_created', 'author_id', 'created_at'),
        Index('ix_tweet_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Tweet(id={self.id}, tweet_id={self.tweet_id}, author_id={self.author_id})>"
