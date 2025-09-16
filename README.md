# Trends\_analysis 🚀

![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![Docker](https://img.shields.io/badge/docker-latest-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

**Trends\_analysis** est une application web pour analyser les tendances sur Twitter (X). Comprenez les sujets qui buzzent, analysez le sentiment des utilisateurs sur la politique, l’économie ou tout autre domaine, et utilisez ces insights pour cibler vos campagnes publicitaires ou prendre des décisions éclairées sur les marchés financiers.

---

## Fonctionnalités principales

* 🔥 Analyse des hashtags par pays et à l’échelle globale
* 📈 Extraction des mots les plus fréquents et tendances émergentes
* 😊😡 Analyse de sentiment sur les tweets (positif, neutre, négatif)
* 🌐 Interface web intuitive pour explorer les données
* 🛠️ Prêt pour intégration avec bases de données et API externes

---

## Stack technique

* **Backend** : FastAPI, Starlette
* **Base de données** : SQLAlchemy
* **HTTP & API** : requests, httpx
* **Analyse de sentiment** : VaderSentiment
* **Configuration** : python-dotenv, pydantic
* **Serveur** : Uvicorn

---

## Installation

Cloner le dépôt et installer les dépendances :

```bash
git clone <URL_DU_REPO>
cd Trends_analysis
make install
```

Lancer l'application en développement :

```bash
make run
```

Lancer dans Docker :

```bash
make docker-build
make docker-run
```

---

## Configuration

Créez un fichier `.env` à la racine du projet avec votre token Twitter (X) :

```env
TWITTER_BEARER_TOKEN=ton_token_ici
```

---

## Utilisation

Accédez à l’interface web : [http://localhost:8000](http://localhost:8000)
Vous pourrez :

1. Rechercher les hashtags tendances par pays ou globalement.
2. Voir les mots-clés les plus utilisés.
3. Analyser le sentiment global des tweets sur un sujet donné.
4. Exporter vos analyses pour vos rapports ou campagnes.

---

## API Endpoints

| Endpoint                 | Méthode | Description                              |
| ------------------------ | ------- | ---------------------------------------- |
| `/trends/global`         | GET     | Liste des hashtags globaux               |
| `/trends/country/{code}` | GET     | Liste des hashtags par pays (`FR`, `US`) |
| `/sentiment/{topic}`     | GET     | Analyse de sentiment pour un mot clé     |
| `/words/{topic}`         | GET     | Mots les plus fréquents pour un sujet    |

**Exemple de réponse :**

```json
{
  "topic": "#Election2025",
  "positive": 45,
  "neutral": 30,
  "negative": 25,
  "top_words": ["vote", "debate", "policy", "economy"]
}
```

---

## Makefile

Automatise les tâches courantes :

```bash
make help          # Affiche cette aide
make install       # Installe les dépendances
make test          # Lance les tests unitaires
make lint          # Vérifie la qualité du code
make format        # Formate le code
make run           # Lance l'application en dev
make docker-build  # Construit l'image Docker
make docker-run    # Lance l'application dans Docker
make clean         # Nettoie les fichiers temporaires
```

---

## Contribuer

Les contributions sont les bienvenues ! 🚀

1. Fork le projet
2. Crée une branche (`feature/ma-fonctionnalité`)
3. Teste tes changements
4. Ouvre une Pull Request

---

## Licence

MIT License – libre à vous de l’utiliser, de l’améliorer ou de vous en inspirer.

---

## Roadmap / Futur

* Visualisations interactives (charts, heatmaps)
* Alertes en temps réel pour hashtags émergents
* Analyse de sentiment plus avancée avec modèles ML
* Dashboard complet pour suivre vos KPI marketing

---

## Screenshots

![UI Example](https://via.placeholder.com/800x400?text=Interface+Trends_analysis)
*Exemple d’interface utilisateur (placeholder)*

![Analytics Example](https://via.placeholder.com/800x400?text=Analytics+Dashboard)
*Exemple de visualisation des tendances*

---

> Avec **Trends\_analysis**, vous ne suivez plus les tendances… vous les anticipez. 😉
