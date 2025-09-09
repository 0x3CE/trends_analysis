# Makefile (pour automatiser les tâches courantes)
.PHONY: help install test lint format run docker-build docker-run clean

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $1, $2}'

install:  ## Installe les dépendances
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:  ## Lance les tests
	pytest app/tests/ -v --cov=app --cov-report=html

lint:  ## Vérifie le code avec flake8 et mypy
	flake8 app/ --max-line-length=88 --ignore=E203,W503
	mypy app/ --ignore-missing-imports

format:  ## Formate le code avec black et isort
	black app/ --line-length=88
	isort app/ --profile black

run:  ## Lance l'application en développement
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:  ## Construit l'image Docker
	docker build -t twitter-collector .

docker-run:  ## Lance l'application dans Docker
	docker run -p 8000:8000 --env-file .env twitter-collector

clean:  ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/