# Service d'analyse d'URL

from app.services.text_analyzer import TextAnalyzer
from app.services.url_security_checker import URLSecurityChecker
from typing import Dict
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLAnalyzer:
    def __init__(self):
        self.text_analyzer = TextAnalyzer()
        self.security_checker = URLSecurityChecker()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info("URLAnalyzer initialisé")
    
    def analyze(self, url: str) -> Dict:
        """
        Analyse une URL pour extraire et vérifier le contenu
        
        Args:
            url: L'URL à analyser
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        try:
            # Vérification de l'URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("URL invalide")
            
            # Extraction du contenu
            content_data = self._extract_content(url)
            
            # Analyse du texte extrait
            if content_data['text']:
                text_analysis = self.text_analyzer.analyze(content_data['text'])
            else:
                text_analysis = {
                    "type": "text",
                    "input": "Contenu non extrait",
                    "detection": {
                        "verdict": "non_analysable",
                        "confidence": 0.0,
                        "is_fake": False,
                        "reasons": ["Impossible d'extraire le contenu de l'URL"]
                    }
                }
            
            # Analyse de la source
            source_analysis = self._analyze_source(url, parsed_url)
            
            # Vérification de sécurité
            security_check = self.security_checker.check_security(url)
            
            return {
                "type": "url",
                "url": url,
                "source": source_analysis,
                "security": security_check,
                "content": content_data,
                "analysis": text_analysis,
                "recommendation": self._generate_url_recommendation(text_analysis, source_analysis, security_check)
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'URL: {e}")
            return {
                "type": "url",
                "url": url,
                "error": str(e),
                "recommendation": "Impossible d'analyser cette URL. Vérifiez qu'elle est accessible et valide."
            }
    
    def _extract_content(self, url: str) -> Dict:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraction du titre
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            # Extraction du contenu principal (articles, paragraphes)
            # Suppression des scripts et styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extraction du texte principal
            paragraphs = soup.find_all(['p', 'article', 'div'])
            text_content = " ".join([p.get_text() for p in paragraphs if p.get_text().strip()])
            
            # Nettoyage du texte
            text_content = " ".join(text_content.split())
            
            # Limitation à 5000 caractères pour l'analyse
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "..."
            
            # Extraction des métadonnées
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ""
            
            return {
                "title": title_text,
                "text": text_content,
                "description": description,
                "length": len(text_content),
                "extracted": True
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            return {
                "title": "",
                "text": "",
                "description": "",
                "length": 0,
                "extracted": False,
                "error": str(e)
            }
    
    def _analyze_source(self, url: str, parsed_url) -> Dict:
        domain = parsed_url.netloc.lower()
        
        # Liste de domaines connus (exemples)
        trusted_domains = [
            'bbc.com', 'reuters.com', 'ap.org', 'theguardian.com',
            'lemonde.fr', 'france24.com', 'franceinfo.fr'
        ]
        
        suspicious_domains = [
            '.blogspot.', '.wordpress.', '.tumblr.', '.weebly.'
        ]
        
        is_trusted = any(trusted in domain for trusted in trusted_domains)
        is_suspicious = any(susp in domain for susp in suspicious_domains)
        
        # Analyse du domaine
        domain_parts = domain.split('.')
        if len(domain_parts) > 3:
            is_suspicious = True
        
        return {
            "domain": domain,
            "is_trusted": is_trusted,
            "is_suspicious": is_suspicious,
            "domain_type": self._classify_domain(domain)
        }
    
    def _classify_domain(self, domain: str) -> str:
        if any(x in domain for x in ['.edu', '.gov', '.org']):
            return "institutionnel"
        elif any(x in domain for x in ['.com', '.net', '.io']):
            return "commercial"
        elif any(x in domain for x in ['.blog', '.news']):
            return "média"
        else:
            return "autre"
    
    def _generate_url_recommendation(self, text_analysis: Dict, source_analysis: Dict, security_check: Dict = None) -> str:
        recommendations = []
        
        # Recommandations de sécurité
        if security_check:
            if security_check.get('is_fraudulent'):
                recommendations.append("🔴 SITE FRAUDULEUX ou NON SÉCURISÉ détecté. Ne visitez pas ce site.")
            elif not security_check.get('is_secure'):
                recommendations.append("⚠️ Site non sécurisé. Évitez de saisir des informations personnelles.")
            elif not security_check.get('ssl', {}).get('has_ssl'):
                recommendations.append("⚠️ Site sans HTTPS. Non sécurisé.")
        
        # Recommandations de source
        if source_analysis.get('is_suspicious'):
            recommendations.append("⚠️ Le domaine de cette source peut être suspect")
        
        if not source_analysis.get('is_trusted'):
            recommendations.append("ℹ️ Cette source n'est pas dans notre liste de sources vérifiées")
        
        # Recommandations de contenu
        if text_analysis.get('detection', {}).get('is_fake'):
            recommendations.append("⚠️ Le contenu présente des signes de désinformation")
        
        if not recommendations:
            recommendations.append("✅ Le contenu et la source semblent fiables")
        
        return " ".join(recommendations)

