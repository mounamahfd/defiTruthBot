# TruthBot

Application web de détection de désinformation par intelligence artificielle développée pour le défi AI4GOOD - Nuit de l'Info.

## Installation

### Avec Docker (recommandé)

```bash
docker-compose up --build -d
```

L'application sera accessible sur http://localhost:8000

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

### Analyse de texte
Détection de désinformation dans un texte avec analyse par IA, vérification de faits et analyse heuristique.

### Analyse d'URL
Vérification du contenu d'une page web, analyse de la source et vérification de sécurité.

### Analyse d'image
Extraction de texte (OCR), détection de manipulations et analyse de deepfake.

## Modèles et outils utilisés

### Analyse de texte

**Modèle IA principal :**
- **DistilBERT** (`distilbert-base-uncased-finetuned-sst-2-english`)
  - Modèle de classification de texte basé sur Transformers
  - Fine-tuné sur le dataset SST-2 (Stanford Sentiment Treebank)
  - Utilisé pour analyser le sentiment et détecter des patterns suspects
  - Chargé via Hugging Face Transformers

**Analyse heuristique :**
- Détection de mots-clés alarmistes
- Analyse de la structure du texte (longueur, ponctuation, majuscules)
- Détection de patterns suspects (affirmations politiques sans source, fausses nouvelles de mort)
- Vérification de la présence de sources et références

**Fact-checking :**
- Recherche web via DuckDuckGo pour vérifier les informations
- Extraction de faits vérifiables du texte
- Analyse des résultats de recherche pour déterminer la véracité
- Base de faits connus pour vérification rapide

**Bibliothèques :**
- `transformers` : Chargement et utilisation du modèle DistilBERT
- `torch` : Backend PyTorch pour l'exécution du modèle
- `requests` : Requêtes HTTP pour la recherche web
- `beautifulsoup4` : Parsing HTML des résultats de recherche

### Analyse d'image

**OCR (Extraction de texte) :**
- **Tesseract OCR** (priorité)
  - Extraction de texte depuis les images
  - Support français et anglais
  - Configuration via `pytesseract`
- **EasyOCR** (alternative)
  - Chargement à la demande pour éviter de bloquer le démarrage
  - Support multilingue amélioré

**Détection de manipulations :**
- **OpenCV** (`cv2`)
  - Détection de visages avec `haarcascade_frontalface_default.xml`
  - Analyse de flou via variance Laplacienne
  - Détection d'incohérences de couleur
- **NumPy**
  - Analyse de variance des pixels
  - Détection de zones suspectes
  - Détection d'artefacts de compression

**Bibliothèques :**
- `pytesseract` : Interface Python pour Tesseract OCR
- `easyocr` : OCR alternatif avec support multilingue
- `opencv-python-headless` : Traitement d'images et vision par ordinateur
- `pillow` (PIL) : Manipulation d'images
- `numpy` : Calculs numériques sur les images

### Analyse d'URL

**Extraction de contenu :**
- **BeautifulSoup**
  - Parsing HTML pour extraire le contenu principal
  - Nettoyage du texte (suppression scripts, styles, navigation)
  - Extraction des métadonnées (titre, description)

**Analyse de texte :**
- Réutilise le `TextAnalyzer` avec le modèle DistilBERT
- Même pipeline d'analyse que pour le texte direct

**Vérification de sécurité :**
- **SSL/TLS checking**
  - Vérification des certificats SSL
  - Validation de la date d'expiration
  - Vérification de la correspondance domaine/certificat
- **Analyse de domaine**
  - Détection de domaines suspects (.tk, .ml, .ga, .cf)
  - Détection de typosquatting
  - Classification du type de domaine (.edu, .gov, .com, etc.)
  - Liste de domaines de confiance (BBC, Reuters, Le Monde, etc.)
- **Vérification de réputation**
  - Résolution DNS
  - Vérification d'accessibilité

**Bibliothèques :**
- `beautifulsoup4` : Parsing HTML
- `requests` : Requêtes HTTP avec gestion de sessions
- `ssl` et `socket` : Vérification SSL/TLS native Python

## Architecture technique

**Backend :**
- FastAPI : Framework web asynchrone
- Uvicorn : Serveur ASGI
- Jinja2 : Templates HTML

**Gestion des modèles :**
- Chargement lazy des analyseurs pour démarrage rapide
- Chargement asynchrone en arrière-plan via ThreadPoolExecutor
- Fallback heuristique si les modèles IA ne sont pas disponibles

**Structure du projet :**
```
app/
├── models/
│   └── fake_news_detector.py    # Modèle DistilBERT et heuristiques
├── services/
│   ├── text_analyzer.py         # Analyse de texte
│   ├── image_analyzer.py        # Analyse d'image
│   ├── url_analyzer.py          # Analyse d'URL
│   ├── fact_checker.py         # Fact-checking web
│   └── url_security_checker.py # Vérification sécurité URL
└── utils/
    └── response_formatter.py    # Formatage des réponses
```

## Technologies principales

- **FastAPI** : Framework web backend
- **Transformers** : Bibliothèque Hugging Face pour les modèles NLP
- **PyTorch** : Framework de deep learning
- **Tesseract/EasyOCR** : Extraction de texte depuis images
- **OpenCV** : Analyse d'images et détection de manipulations
- **BeautifulSoup** : Parsing HTML
- **Docker** : Containerisation

## Notes importantes

- Le modèle DistilBERT est téléchargé depuis Hugging Face au premier démarrage (peut prendre plusieurs minutes)
- L'application fonctionne en mode heuristique si les modèles IA ne sont pas disponibles
- EasyOCR est chargé à la demande pour éviter de bloquer le démarrage
- Les analyses peuvent prendre du temps selon la complexité du contenu

## Auteur

Développé pour le défi AI4GOOD - Nuit de l'Info
