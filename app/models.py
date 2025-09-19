# app/models.py
"""Database models for the Twitter/X collector application.

### 🎯 Objectif principal

Définir les **modèles ORM SQLAlchemy** pour stocker les tweets collectés depuis Twitter/X.

---

### 🗂️ Modèle principal : `Tweet`

* **Table** : `tweets`

* **Colonnes** :

  * `id` : entier auto-incrémenté, clé primaire.
  * `tweet_id` : string unique, identifiant Twitter du tweet.
  * `author_id` : string, identifiant de l’auteur du tweet (nullable).
  * `text` : contenu textuel du tweet (non nullable).
  * `created_at` : datetime de création du tweet (nullable).
  * `collected_at` : datetime automatique de collecte (`func.now()`).
  * `raw_json` : JSON brut retourné par l’API Twitter (nullable).

* **Index** :

  * `ix_tweet_author_created` → composite sur `author_id` + `created_at` pour accélérer les requêtes par auteur/date.
  * `ix_tweet_created` → sur `created_at` pour les tris/filtrages temporels fréquents.

* **Représentation (`__repr__`)**

  * Retourne un résumé pratique pour le logging/debug :

    ```
    <Tweet(id=1, tweet_id=123, author_id=456)>
    ```

---

### 🔑 Points clés

* Optimisé pour **recherches fréquentes sur la date et l’auteur**.
* Stocke **texte brut et JSON** → permet analyses ultérieures (analytics, hashtags, sentiment).
* Compatible avec `TweetService` pour insertion et récupération.
* Compatible avec `AnalyticsService` pour analyser volume et hashtags.

---

En résumé : **c’est le cœur du modèle de données**, la table unique qui alimente à la fois la collecte et l’analyse des tweets.

Si tu veux, Patron, je peux maintenant te faire **le schéma complet du fonctionnement de ton application** : comment tous les fichiers que tu m’as envoyés s’imbriquent, flux des données, services, routes et DB.
Veux-tu que je fasse ça maintenant ?

"""
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
