# app/schemas.py
"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class TweetCreate(BaseModel):
    """Schema pour la création d'un nouveau tweet."""
    model_config = ConfigDict(from_attributes=True) # or other config options
    tweet_id: str = Field(..., description="ID unique du tweet")
    author_id: Optional[str] = Field(None, description="ID de l'auteur")
    text: str = Field(..., min_length=1, description="Contenu du tweet")
    created_at: Optional[datetime] = Field(None, description="Date de création")
    raw_json: Optional[str] = Field(None, description="JSON brut de l'API")


class TweetRead(BaseModel):
    """Schema pour la lecture d'un tweet."""
    id: int
    tweet_id: str
    author_id: Optional[str]
    text: str
    created_at: Optional[datetime]
    collected_at: datetime
    
    class Config:
        orm_mode = True


class CollectRequest(BaseModel):
    """Schema pour les requêtes de collecte de tweets."""
    query: str = Field(..., min_length=1, description="Requête de recherche")
    max_results: Optional[int] = Field(
        default=10, 
        ge=1, 
        le=100, 
        description="Nombre maximum de résultats (1-100)"
    )


class HashtagAnalysis(BaseModel):
    """Schema pour l'analyse des hashtags."""
    hashtag: str
    count: int


class VolumeAnalysis(BaseModel):
    """Schema pour l'analyse du volume par heure."""
    hour_or_key: str
    count: int


class AnalyticsResponse(BaseModel):
    """Schema de réponse pour les analytics."""
    top_hashtags: Optional[List[HashtagAnalysis]] = None
    volume_by_hour: Optional[List[VolumeAnalysis]] = None