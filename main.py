from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from pathlib import Path
import uvicorn
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

app.mount("/static", StaticFiles(directory="static"), name="static")
TEMPLATES_DIR = Path("templates")

text_analyzer = None
url_analyzer = None
image_analyzer = None

def get_text_analyzer():
    global text_analyzer
    if text_analyzer is None:
        text_analyzer = TextAnalyzer()
    return text_analyzer

def get_url_analyzer():
    global url_analyzer
    if url_analyzer is None:
        url_analyzer = URLAnalyzer()
    return url_analyzer

def get_image_analyzer():
    global image_analyzer
    if image_analyzer is None:
        image_analyzer = ImageAnalyzer()
    return image_analyzer

@app.on_event("startup")
async def startup_event():
    import asyncio
    import logging
    from concurrent.futures import ThreadPoolExecutor
    
    logger = logging.getLogger(__name__)
    logger.info("Démarrage du serveur - chargement des modèles en arrière-plan...")
    
    def load_analyzers_sync():
        try:
            logger.info("Chargement de TextAnalyzer...")
            get_text_analyzer()
            logger.info("TextAnalyzer chargé")
        except Exception as e:
            logger.error(f"Erreur chargement TextAnalyzer: {e}")
        
        try:
            logger.info("Chargement de URLAnalyzer...")
            get_url_analyzer()
            logger.info("URLAnalyzer chargé")
        except Exception as e:
            logger.error(f"Erreur chargement URLAnalyzer: {e}")
        
        try:
            logger.info("Chargement de ImageAnalyzer...")
            get_image_analyzer()
            logger.info("ImageAnalyzer chargé")
        except Exception as e:
            logger.error(f"Erreur chargement ImageAnalyzer: {e}")
        
        logger.info("Tous les analyseurs sont prêts!")
    
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    loop.run_in_executor(executor, load_analyzers_sync)


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
        
        analyzer = get_text_analyzer()
        result = analyzer.analyze(text)
        return format_response(result, "text")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@app.post("/api/analyze/url")
async def analyze_url(url: str = Form(...)):
    try:
        if not url or not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL invalide")
        
        analyzer = get_url_analyzer()
        result = analyzer.analyze(url)
        return format_response(result, "url")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@app.post("/api/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        image_data = await file.read()
        analyzer = get_image_analyzer()
        result = analyzer.analyze(image_data)
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

