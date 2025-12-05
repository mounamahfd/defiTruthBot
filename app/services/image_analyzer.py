try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

import io
import os
from typing import Dict, Optional
import logging

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

EASYOCR_AVAILABLE = None
easyocr = None

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageAnalyzer:
    def __init__(self):
        if TESSERACT_AVAILABLE:
            import os
            tesseract_cmd = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                logger.info(f"Tesseract configuré: {tesseract_cmd}")
            else:
                logger.warning(f"Tesseract non trouvé à {tesseract_cmd}")
        
        self.easyocr_reader = None
        self._easyocr_available = None
    
    def analyze(self, image_data: bytes) -> Dict:
        """
        Analyse une image pour détecter les manipulations
        
        Args:
            image_data: Données binaires de l'image
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        if not PIL_AVAILABLE:
            return {
                "type": "image",
                "error": "PIL/Pillow n'est pas installé. Installez-le avec: pip install pillow",
                "recommendation": "Installez Pillow pour analyser les images: pip install pillow"
            }
        
        try:
            image = Image.open(io.BytesIO(image_data))
            image_info = self._analyze_image_properties(image)
            manipulation_signs = self._detect_manipulation_signs(image)
            deepfake_analysis = self._detect_deepfake(image)
            text_extracted = self._extract_text_ocr(image)
            
            text_analysis = None
            if text_extracted and len(text_extracted.strip()) > 10:
                from app.services.text_analyzer import TextAnalyzer
                text_analyzer = TextAnalyzer()
                text_analysis = text_analyzer.analyze(text_extracted)
            
            return {
                "type": "image",
                "image_info": image_info,
                "manipulation_signs": manipulation_signs,
                "deepfake_analysis": deepfake_analysis,
                "text_extracted": text_extracted,
                "text_analysis": text_analysis,
                "ocr_available": TESSERACT_AVAILABLE or EASYOCR_AVAILABLE,
                "recommendation": self._generate_image_recommendation(
                    manipulation_signs, deepfake_analysis, text_analysis
                )
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image: {e}")
            return {
                "type": "image",
                "error": str(e),
                "recommendation": "Impossible d'analyser cette image. Vérifiez le format (JPG, PNG, etc.)"
            }
    
    def _analyze_image_properties(self, image: Image.Image) -> Dict:
        return {
            "format": image.format,
            "size": image.size,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "aspect_ratio": image.width / image.height if image.height > 0 else 0
        }
    
    def _detect_manipulation_signs(self, image: Image.Image) -> Dict:
        if not NUMPY_AVAILABLE:
            return {
                "suspicious_areas": 0,
                "compression_artifacts": False,
                "inconsistencies": False,
                "confidence": 0.3
            }
        
        img_array = np.array(image.convert('RGB'))
        signs = {
            "suspicious_areas": 0,
            "compression_artifacts": False,
            "inconsistencies": False,
            "confidence": 0.3
        }
        
        if len(img_array.shape) == 3:
            variance = np.var(img_array, axis=2)
            high_variance_areas = np.sum(variance > np.percentile(variance, 95))
            
            if high_variance_areas > (image.width * image.height * 0.1):
                signs["suspicious_areas"] = 1
                signs["confidence"] = 0.5
        
        return signs
    
    def _detect_deepfake(self, image: Image.Image) -> Dict:
        result = {
            "deepfake_detected": False,
            "confidence": 0.0,
            "method": "basique",
            "details": []
        }
        
        if not NUMPY_AVAILABLE or not CV2_AVAILABLE:
            result["details"].append("OpenCV non disponible - analyse basique uniquement")
            return result
        
        try:
            img_array = np.array(image.convert('RGB'))
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                result["details"].append(f"{len(faces)} visage(s) détecté(s)")
                
                for (x, y, w, h) in faces:
                    face_roi = img_cv[y:y+h, x:x+w]
                    face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                    laplacian_var = cv2.Laplacian(face_gray, cv2.CV_64F).var()
                    
                    if laplacian_var < 100:
                        result["deepfake_detected"] = True
                        result["confidence"] = 0.6
                        result["details"].append("Flou suspect détecté dans la zone du visage")
                    
                    if len(face_roi.shape) == 3:
                        color_variance = np.var(face_roi, axis=2)
                        if np.mean(color_variance) > 500:
                            result["confidence"] = min(result["confidence"] + 0.2, 0.9)
                            result["details"].append("Incohérences de couleur détectées")
            else:
                result["details"].append("Aucun visage détecté - analyse générale")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la détection de deepfake: {e}")
            result["details"].append(f"Erreur: {str(e)}")
        
        return result
    
    def _check_easyocr_available(self):
        if self._easyocr_available is None:
            try:
                import easyocr
                self._easyocr_available = True
                logger.info("EasyOCR disponible")
            except (ImportError, AttributeError) as e:
                self._easyocr_available = False
                logger.info(f"EasyOCR non disponible: {e}")
        return self._easyocr_available
    
    def _extract_text_ocr(self, image: Image.Image) -> str:
        text = ""
        
        if self._check_easyocr_available():
            if self.easyocr_reader is None:
                try:
                    import easyocr
                    logger.info("Chargement EasyOCR à la demande...")
                    self.easyocr_reader = easyocr.Reader(['fr', 'en'], gpu=False, verbose=False)
                    logger.info("EasyOCR chargé avec succès")
                except Exception as e:
                    logger.warning(f"Erreur chargement EasyOCR: {e}")
                    self.easyocr_reader = False
            
            if self.easyocr_reader and self.easyocr_reader is not False:
                try:
                    logger.info("Extraction de texte avec EasyOCR...")
                    results = self.easyocr_reader.readtext(np.array(image))
                    text = " ".join([result[1] for result in results if result[2] > 0.5])
                    if text:
                        logger.info(f"Texte extrait avec EasyOCR: {len(text)} caractères")
                        return text
                except Exception as e:
                    logger.warning(f"Erreur avec EasyOCR: {e}")
        
        if TESSERACT_AVAILABLE:
            try:
                logger.info("Extraction de texte avec Tesseract...")
                text = pytesseract.image_to_string(image, lang='fra+eng')
                if text and text.strip():
                    logger.info(f"Texte extrait avec Tesseract: {len(text)} caractères")
                    return text.strip()
            except Exception as e:
                logger.warning(f"Erreur avec Tesseract: {e}")
        
        if not text:
            if not TESSERACT_AVAILABLE and not (self._easyocr_available if self._easyocr_available is not None else False):
                return "⚠️ OCR non disponible. Installez Tesseract ou EasyOCR:\n" \
                       "- Tesseract: pip install pytesseract (nécessite aussi Tesseract installé)\n" \
                       "- EasyOCR: pip install easyocr"
            else:
                return "Aucun texte détecté dans l'image"
        
        return text
    
    def _generate_image_recommendation(
        self, 
        manipulation_signs: Dict, 
        deepfake_analysis: Dict,
        text_analysis: Optional[Dict] = None
    ) -> str:
        recommendations = []
        
        if deepfake_analysis.get("deepfake_detected"):
            confidence = deepfake_analysis.get("confidence", 0) * 100
            recommendations.append(f"🔴 Deepfake probable détecté (confiance: {confidence:.1f}%)")
            if deepfake_analysis.get("details"):
                recommendations.append(f"Détails: {', '.join(deepfake_analysis['details'][:2])}")
        
        if manipulation_signs.get("suspicious_areas", 0) > 0:
            recommendations.append("⚠️ Des zones suspectes ont été détectées dans l'image")
        
        if text_analysis and text_analysis.get('detection', {}).get('is_fake'):
            reliability = text_analysis.get('detection', {}).get('reliability', 0)
            recommendations.append(f"🔴 Le texte extrait présente des signes de désinformation (fiabilité: {reliability:.1f}%)")
        
        if not recommendations:
            if deepfake_analysis.get("method") == "basique":
                recommendations.append("ℹ️ Analyse basique effectuée. Pour une détection approfondie de deepfake, " \
                                     "installez OpenCV et des modèles spécialisés (FaceForensics++, etc.)")
            else:
                recommendations.append("✅ Aucun signe majeur de manipulation détecté")
        
        return " ".join(recommendations)
