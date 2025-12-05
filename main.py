# TruthBot - Application principale

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from pathlib import Path
import uvicorn
from typing import Optional
import os

from app.services.text_analyzer import TextAnalyzer
from app.services.url_analyzer import URLAnalyzer
from app.services.image_analyzer import ImageAnalyzer
from app.utils.response_formatter import format_response

app = FastAPI(
    title="TruthBot",
    description="Détection de désinformation par IA - Défi AI4GOOD",
    version="1.0.0"
)

# Configuration des fichiers statiques et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
TEMPLATES_DIR = Path("templates")

# Initialisation des analyseurs
text_analyzer = TextAnalyzer()
url_analyzer = URLAnalyzer()
image_analyzer = ImageAnalyzer()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    template_path = TEMPLATES_DIR / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())
    return HTMLResponse(content=template.render())


@app.post("/api/analyze/text")
async def analyze_text(text: str = Form(...)):
    try:
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Le texte doit contenir au moins 10 caractères")
        
        result = text_analyzer.analyze(text)
        return format_response(result, "text")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@app.post("/api/analyze/url")
async def analyze_url(url: str = Form(...)):
    try:
        if not url or not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL invalide")
        
        result = url_analyzer.analyze(url)
        return format_response(result, "url")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@app.post("/api/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        # Lire le contenu de l'image
        image_data = await file.read()
        result = image_analyzer.analyze(image_data)
        return format_response(result, "image")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "TruthBot",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

