# Service d'analyse de texte

from app.models.fake_news_detector import FakeNewsDetector
from app.services.fact_checker import FactChecker
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextAnalyzer:
    def __init__(self):
        self.detector = FakeNewsDetector()
        self.fact_checker = FactChecker()
        logger.info("TextAnalyzer initialisé")
    
    def analyze(self, text: str) -> Dict:
        """
        Analyse un texte pour détecter la désinformation
        
        Args:
            text: Le texte à analyser
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        try:
            # Détection de fake news
            detection_result = self.detector.detect_fake_news(text)
            
            # Vérification contre faits connus (priorité)
            known_facts_check = self.fact_checker.check_against_known_facts(text)
            
            # Vérification de faits (fact-checking web)
            fact_check = self.fact_checker.verify_fact(text)
            
            # Analyse de sentiment (pour détecter les biais)
            sentiment = self._analyze_sentiment(text)
            
            # Métriques du texte
            metrics = self._calculate_metrics(text)
            
            # Ajuster le score de détection avec la vérification de faits
            # PRIORITÉ à la recherche web (fact_check), puis faits connus comme fallback
            if fact_check.get("verified") is False and fact_check.get("confidence", 0) > 0.5:
                # Vérifié comme FAUX par recherche web
                detection_result["confidence"] = min(1.0, detection_result["confidence"] + 0.3)
                detection_result["is_fake"] = True
                detection_result["verdict"] = "fake"
                detection_result["reliability"] = (1.0 - detection_result["confidence"]) * 100
            elif fact_check.get("verified") is True and fact_check.get("confidence", 0) > 0.5:
                # Vérifié comme VRAI par recherche web
                detection_result["confidence"] = max(0.0, detection_result["confidence"] - 0.35)
                detection_result["is_fake"] = False
                detection_result["verdict"] = "probablement_vrai"
                detection_result["reliability"] = (1.0 - detection_result["confidence"]) * 100
            elif known_facts_check.get("verified_as_true"):
                # Fallback : fait connu vérifié (seulement si recherche web n'a pas donné de résultat)
                detection_result["confidence"] = max(0.0, detection_result["confidence"] - 0.3)
                detection_result["is_fake"] = False
                detection_result["verdict"] = "probablement_vrai"
                detection_result["reliability"] = (1.0 - detection_result["confidence"]) * 100
            elif known_facts_check.get("verified_as_false"):
                # Fallback : fait connu comme faux
                detection_result["confidence"] = min(1.0, detection_result["confidence"] + 0.25)
                detection_result["is_fake"] = True
                detection_result["verdict"] = "fake"
                detection_result["reliability"] = (1.0 - detection_result["confidence"]) * 100
            
            # Recalculer la fiabilité
            detection_result["reliability"] = (1.0 - detection_result["confidence"]) * 100
            
            return {
                "type": "text",
                "input": text[:200] + "..." if len(text) > 200 else text,
                "detection": detection_result,
                "fact_check": fact_check,
                "known_facts": known_facts_check,
                "sentiment": sentiment,
                "metrics": metrics,
                "recommendation": self._generate_recommendation(detection_result, sentiment, fact_check, known_facts_check)
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du texte: {e}")
            raise
    
    def _analyze_sentiment(self, text: str) -> Dict:
        # Analyse simple basée sur des mots-clés
        text_lower = text.lower()
        
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'negative', 'failure', 'sad', 'horrible']
        neutral_words = ['fact', 'information', 'data', 'report', 'study']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)
        
        total = positive_count + negative_count + neutral_count
        if total == 0:
            sentiment = "neutral"
            score = 0.5
        elif positive_count > negative_count:
            sentiment = "positive"
            score = 0.5 + (positive_count / max(total, 1)) * 0.3
        elif negative_count > positive_count:
            sentiment = "negative"
            score = 0.5 - (negative_count / max(total, 1)) * 0.3
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "label": sentiment,
            "score": float(score),
            "bias_detected": abs(score - 0.5) > 0.3
        }
    
    def _calculate_metrics(self, text: str) -> Dict:
        words = text.split()
        sentences = text.split('.')
        
        return {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_words_per_sentence": len(words) / max(len([s for s in sentences if s.strip()]), 1),
            "char_count": len(text),
            "readability": "facile" if len(words) < 20 else "moyen" if len(words) < 50 else "complexe"
        }
    
    def _generate_recommendation(self, detection: Dict, sentiment: Dict, fact_check: Dict = None, known_facts: Dict = None) -> str:
        recommendations = []
        
        # PRIORITÉ à la recherche web (fact_check)
        if fact_check and fact_check.get("verified") is False:
            recommendations.append(f"🔴 Information vérifiée comme FAUSSE par recherche web (confiance: {fact_check.get('confidence', 0)*100:.0f}%).")
        elif fact_check and fact_check.get("verified") is True:
            recommendations.append(f"✅ Information vérifiée comme VRAIE par recherche web (confiance: {fact_check.get('confidence', 0)*100:.0f}%).")
        elif fact_check and fact_check.get("sources_found", 0) > 0:
            recommendations.append(f"ℹ️ {fact_check.get('sources_found', 0)} source(s) fiable(s) trouvée(s) mais verdict incertain.")
        # Fallback : faits connus (seulement si recherche web n'a pas fonctionné)
        elif known_facts and known_facts.get("verified_as_true"):
            recommendations.append("✅ Information vérifiée comme VRAIE (base de faits - recherche web indisponible).")
        elif known_facts and known_facts.get("verified_as_false"):
            recommendations.append("🔴 Information vérifiée comme FAUSSE (base de faits - recherche web indisponible).")
        
        if detection['is_fake']:
            recommendations.append("⚠️ Ce contenu présente des signes de désinformation. Vérifiez les sources.")
        elif detection['confidence'] > 0.5:
            recommendations.append("⚠️ Ce contenu nécessite une vérification approfondie.")
        elif sentiment['bias_detected']:
            recommendations.append("ℹ️ Ce contenu présente un biais émotionnel.")
        else:
            recommendations.append("✓ Ce contenu semble fiable, mais restez critique.")
        
        return " ".join(recommendations) if recommendations else "ℹ️ Analyse effectuée."

