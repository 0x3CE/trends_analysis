# app/schemas.py
"""Pydantic schemas for request/response validation.

### 🎯 Objectif principal

Définir les **schemas Pydantic** pour valider et formater les **requêtes et réponses** de ton API FastAPI.
Ces schemas permettent de garantir la cohérence des données échangées entre les routes, les services et les clients API.

---

### 🗂️ Les principaux schemas

1. **`TweetCreate`**

   * Pour créer un tweet (internes ou tests).
   * Champs : `tweet_id`, `author_id`, `text`, `created_at`, `raw_json`.
   * `model_config = ConfigDict(from_attributes=True)` → permet la conversion automatique depuis un objet ORM.

2. **`TweetRead`**

   * Pour retourner un tweet aux clients API.
   * Champs : `id`, `tweet_id`, `author_id`, `text`, `created_at`, `collected_at`.
   * `orm_mode = True` → permet de convertir un objet SQLAlchemy directement en Pydantic.

3. **`CollectRequest`**

   * Pour la route de collecte (`POST /tweets/collect`).
   * Champs : `query` (string obligatoire), `max_results` (1-100, défaut 10).

4. **`HashtagAnalysis`**

   * Représente un hashtag et son compteur.
   * Champs : `hashtag` (str), `count` (int).

5. **`VolumeAnalysis`**

   * Représente le volume de tweets pour un créneau horaire.
   * Champs : `hour_or_key` (str), `count` (int).

6. **`AnalyticsResponse`**

   * Réponse globale pour les endpoints analytics (`/analytics`).
   * Champs optionnels : `top_hashtags` (liste de `HashtagAnalysis`), `volume_by_hour` (liste de `VolumeAnalysis`).

---

### 🔑 Points clés

* Garantit que l’API renvoie toujours **des objets bien formés**.
* Sert de **contrat clair** entre routes, services et front-end.
* Compatible avec `TweetService` et `AnalyticsService` pour la conversion ORM → API.

---

Si tu veux, Patron, je peux maintenant te faire **le schéma complet de l’architecture** et expliquer **le flow des données** entre tous ces fichiers : collecte, stockage, analyse, et retour via l’API.
Veux-tu que je fasse ça maintenant ?

"""
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