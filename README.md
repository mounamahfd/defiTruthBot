# TruthBot

Application web de détection de désinformation par intelligence artificielle.

## Installation

### Avec Docker (recommandé)

```bash
docker-compose up --build
```

### Installation locale

```bash
pip install -r requirements.txt
python main.py
```

## Utilisation

### Local

Accéder à l'application : http://localhost:8000

### Déploiement

Voir [DEPLOY.md](DEPLOY.md) pour les instructions de déploiement.

Options disponibles :
- Railway (recommandé)
- Render
- Fly.io
- DigitalOcean
- VPS avec Docker

## Fonctionnalités

- **Texte** : Analyser un texte pour détecter la désinformation (recherche web + IA)
- **URL** : Vérifier le contenu d'une page web et sa sécurité
- **Image** : Analyser une image (OCR + détection de manipulations)

## Technologies

- FastAPI (backend)
- Transformers (IA)
- Tesseract/EasyOCR (extraction de texte)
- OpenCV (analyse d'images)

## Auteur

Développé pour le défi AI4GOOD - Nuit de l'Info
