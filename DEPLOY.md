# Guide de déploiement - TruthBot

## Options de déploiement

### 1. Railway (Recommandé - Simple et gratuit)

1. Créez un compte sur [Railway](https://railway.app)
2. Cliquez sur "New Project"
3. Sélectionnez "Deploy from GitHub repo" (ou "Deploy from Dockerfile")
4. Connectez votre repository GitHub
5. Railway détectera automatiquement le `Dockerfile`
6. L'application sera déployée automatiquement

**Variables d'environnement** (optionnel, configurées dans Railway Dashboard):
- `PYTHONUNBUFFERED=1`
- `TESSERACT_CMD=/usr/bin/tesseract`

### 2. Render

1. Créez un compte sur [Render](https://render.com)
2. Cliquez sur "New +" > "Web Service"
3. Connectez votre repository GitHub
4. Sélectionnez le repository
5. Render utilisera automatiquement le `render.yaml`
6. Cliquez sur "Create Web Service"

### 3. Fly.io

1. Installez Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Créez un compte: `fly auth signup`
3. Déployez: `fly launch` (utilisera automatiquement `fly.toml`)
4. Suivez les instructions

### 4. DigitalOcean App Platform

1. Créez un compte sur [DigitalOcean](https://www.digitalocean.com)
2. Allez dans "App Platform"
3. Cliquez sur "Create App"
4. Connectez votre repository GitHub
5. Sélectionnez "Dockerfile" comme type de build
6. Configurez les variables d'environnement si nécessaire

### 5. VPS (Ubuntu/Debian)

```bash
# Sur votre serveur
git clone <votre-repo>
cd defiTrab
docker-compose up -d --build
```

## Variables d'environnement

Ces variables sont optionnelles mais peuvent être configurées:

- `PYTHONUNBUFFERED=1` - Pour les logs en temps réel
- `TESSERACT_CMD=/usr/bin/tesseract` - Chemin vers Tesseract
- `HF_HUB_DOWNLOAD_TIMEOUT=120` - Timeout pour Hugging Face

## Notes importantes

- Le premier démarrage peut prendre du temps (téléchargement des modèles IA)
- L'application fonctionne même si EasyOCR n'est pas disponible (utilise Tesseract)
- Le modèle Hugging Face sera téléchargé automatiquement au premier lancement
- Assurez-vous que le port 8000 est accessible

## Vérification du déploiement

Une fois déployé, testez:
- `https://votre-domaine.com/api/health` - Health check
- `https://votre-domaine.com/` - Interface web

