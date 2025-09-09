# Dockerfile (amélioré)
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="dev-team"
LABEL description="Twitter/X Collector API"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Création d'un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système si nécessaires
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY app ./app

# Changement de propriétaire vers l'utilisateur non-root
RUN chown -R appuser:appuser /app
USER appuser

# Configuration par défaut
ENV DATABASE_URL=sqlite:///./tweets.db
ENV DEBUG=false

# Port d'exposition
EXPOSE 8000

# Commande de démarrage avec configuration de production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]