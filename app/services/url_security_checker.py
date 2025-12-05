import requests
import ssl
import socket
import re
from urllib.parse import urlparse
from typing import Dict, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLSecurityChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Domaines suspects connus
        self.suspicious_domains = [
            '.tk', '.ml', '.ga', '.cf',  # Domaines gratuits souvent utilisés pour fraudes
            '.xyz', '.top', '.click', '.download'  # Domaines souvent utilisés pour spam
        ]
        
        # Domaines de confiance
        self.trusted_domains = [
            'bbc.com', 'reuters.com', 'ap.org', 'theguardian.com',
            'lemonde.fr', 'france24.com', 'franceinfo.fr', 'lefigaro.fr',
            'nytimes.com', 'washingtonpost.com', 'cnn.com'
        ]
    
    def check_security(self, url: str) -> Dict:
        """
        Vérifie la sécurité et la légitimité d'une URL
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            ssl_check = self._check_ssl(domain, parsed.scheme == 'https')
            domain_check = self._check_domain(domain)
            reputation_check = self._check_reputation(domain)
            age_check = self._check_domain_age(domain)
            
            security_score = self._calculate_security_score(
                ssl_check, domain_check, reputation_check, age_check
            )
            
            is_secure = security_score >= 0.6
            is_fraudulent = security_score < 0.4
            
            return {
                "url": url,
                "domain": domain,
                "is_secure": is_secure,
                "is_fraudulent": is_fraudulent,
                "security_score": float(security_score),
                "ssl": ssl_check,
                "domain": domain_check,
                "reputation": reputation_check,
                "age": age_check,
                "recommendation": self._generate_security_recommendation(
                    is_secure, is_fraudulent, security_score, ssl_check, domain_check
                )
            }
        
        except Exception as e:
            logger.error(f"Erreur vérification sécurité URL: {e}")
            return {
                "url": url,
                "error": str(e),
                "is_secure": False,
                "security_score": 0.0
            }
    
    def _check_ssl(self, domain: str, is_https: bool) -> Dict:
        """
        Vérifie le certificat SSL/TLS
        """
        if not is_https:
            return {
                "has_ssl": False,
                "valid": False,
                "error": "Pas de HTTPS"
            }
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    is_valid = datetime.now() < not_after
                    
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    return {
                        "has_ssl": True,
                        "valid": is_valid,
                        "expires": cert['notAfter'],
                        "issuer": issuer.get('organizationName', 'Unknown'),
                        "subject": subject.get('commonName', domain)
                    }
        except ssl.SSLError as e:
            return {
                "has_ssl": True,
                "valid": False,
                "error": f"Erreur SSL: {str(e)}"
            }
        except Exception as e:
            return {
                "has_ssl": False,
                "valid": False,
                "error": f"Impossible de vérifier SSL: {str(e)}"
            }
    
    def _check_domain(self, domain: str) -> Dict:
        """
        Vérifie le domaine pour détecter les fraudes
        """
        is_suspicious = False
        is_trusted = False
        reasons = []
        
        for suspicious in self.suspicious_domains:
            if suspicious in domain:
                is_suspicious = True
                reasons.append(f"Domaine suspect détecté: {suspicious}")
        
        for trusted in self.trusted_domains:
            if trusted in domain:
                is_trusted = True
                reasons.append(f"Domaine de confiance: {trusted}")
                break
        
        if self._detect_typosquatting(domain):
            is_suspicious = True
            reasons.append("Possible typosquatting détecté")
        
        if len(domain) > 50:
            is_suspicious = True
            reasons.append("Domaine très long (suspect)")
        
        return {
            "is_suspicious": is_suspicious,
            "is_trusted": is_trusted,
            "reasons": reasons
        }
    
    def _detect_typosquatting(self, domain: str) -> bool:
        suspicious_patterns = [
            r'[a-z]{2,}[-_][a-z]{2,}',  # Domaines avec tirets multiples
            r'\d+[a-z]+\d+',  # Mélange de chiffres et lettres suspect
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain):
                return True
        
        return False
    
    def _check_reputation(self, domain: str) -> Dict:
        checks = {
            "has_ip": False,
            "is_accessible": False
        }
        
        try:
            ip = socket.gethostbyname(domain)
            checks["has_ip"] = True
            checks["ip"] = ip
            
            try:
                response = self.session.get(f"https://{domain}", timeout=5, allow_redirects=True)
                checks["is_accessible"] = response.status_code == 200
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Erreur vérification réputation: {e}")
        
        return checks
    
    def _check_domain_age(self, domain: str) -> Dict:
        return {
            "age_verified": False,
            "note": "Vérification d'âge non disponible sans API whois"
        }
    
    def _calculate_security_score(self, ssl_check: Dict, domain_check: Dict, 
                                  reputation_check: Dict, age_check: Dict) -> float:
        score = 0.5
        
        if ssl_check.get("has_ssl") and ssl_check.get("valid"):
            score += 0.3
        elif ssl_check.get("has_ssl"):
            score += 0.1
        else:
            score -= 0.2
        
        if domain_check.get("is_trusted"):
            score += 0.2
        elif domain_check.get("is_suspicious"):
            score -= 0.3
        
        if reputation_check.get("is_accessible"):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_security_recommendation(self, is_secure: bool, is_fraudulent: bool,
                                         security_score: float, ssl_check: Dict, 
                                         domain_check: Dict) -> str:
        if is_fraudulent:
            return "🔴 Site potentiellement frauduleux ou non sécurisé. Ne partagez pas d'informations personnelles."
        elif not ssl_check.get("has_ssl"):
            return "⚠️ Site non sécurisé (pas de HTTPS). Évitez de saisir des informations sensibles."
        elif not ssl_check.get("valid"):
            return "⚠️ Certificat SSL invalide ou expiré. Site potentiellement dangereux."
        elif domain_check.get("is_suspicious"):
            return "⚠️ Domaine suspect détecté. Vérifiez l'authenticité du site avant de continuer."
        elif is_secure:
            return "✅ Site sécurisé et légitime."
        else:
            return "ℹ️ Site à vérifier. Consultez d'autres sources avant de faire confiance."

