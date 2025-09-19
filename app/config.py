# app/config.py
"""Configuration management for the Twitter/X collector application.

* **Rôle global** : gérer toute la **configuration de l’application** (DB, API Twitter/X, options d’exécution).
  👉 C’est la source de vérité centrale pour les paramètres, avec support des variables d’environnement et `.env`.

* **Classe `Settings` (hérite de `BaseSettings` de Pydantic)** :

  * **DB** :

    * `database_url` (par défaut SQLite `./tweets.db`).
  * **Twitter/X API** :

    * `x_api_base` (par défaut `https://api.x.com/2`).
    * `bearer_token` (peut venir de l’env var `BEARER_TOKEN`).
  * **App** :

    * `app_name` = "Twitter/X Collector".
    * `debug` = False.
  * **Test mode** :

    * `testing` détecté automatiquement (si `TESTING=true`, ou si exécution via `pytest`).

* **Méthodes utilitaires** :

  * `is_sqlite()` → True si la DB est SQLite.
  * `is_memory_db()` → True si c’est une base en mémoire (`:memory:`).

* **Config interne (`class Config`)** :

  * Lit les variables dans `.env`.
  * Pas sensible à la casse (`case_sensitive = False`).

* **Instance globale** :

  * `settings = Settings()` → dispo partout dans l’app.

👉 En résumé : ce fichier est le **hub de configuration** qui alimente le client Twitter (`bearer_token`, `x_api_base`), la base (`database_url`), et le mode d’exécution (`debug`, `testing`).

Tu veux que je résume ensuite la partie **`database`** (vu qu’on commence à toucher à la config/infra) ?

"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""
    
    # Database configuration
    database_url: str = "sqlite:///./tweets.db"
    
    # Twitter/X API configuration
    x_api_base: str = "https://api.x.com/2"
    bearer_token: Optional[str] = None
    
    # Application configuration
    app_name: str = "Twitter/X Collector"
    debug: bool = False
    
    # Test mode detection (automatiquement détecté)
    testing: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Détection automatique du mode test
        self.testing = (
            os.getenv("TESTING", "").lower() == "true" or
            "pytest" in os.getenv("_", "") or
            "pytest" in str(os.getenv("PYTEST_CURRENT_TEST", ""))
        )
    
    def is_sqlite(self) -> bool:
        """Vérifie si on utilise SQLite."""
        return self.database_url.startswith("sqlite")
    
    def is_memory_db(self) -> bool:
        """Vérifie si on utilise une base en mémoire (pour les tests)."""
        return ":memory:" in self.database_url


settings = Settings()