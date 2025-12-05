# Service de vérification de faits (fact-checking)

import requests
import logging
from typing import Dict, List, Optional
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FactChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def verify_fact(self, text: str) -> Dict:
        """
        Vérifie la véracité d'une information en cherchant sur Internet
        """
        if not text or len(text.strip()) < 10:
            return {
                "verified": None,
                "confidence": 0.0,
                "sources": [],
                "method": "insufficient_text"
            }
        
        # Recherche web directe sur le texte complet
        search_result = self._search_web(text)
        
        # Analyse des résultats de recherche
        if search_result.get("sources_found", 0) > 0:
            # Analyser les résultats pour déterminer si l'info est vraie ou fausse
            analysis = self._analyze_search_results(text, search_result)
            return {
                "verified": analysis.get("verified"),
                "confidence": analysis.get("confidence", 0.5),
                "sources": search_result.get("sources", []),
                "method": "web_search",
                "search_query": search_result.get("query"),
                "results_count": search_result.get("results_count", 0)
            }
        
        # Fallback : extraction de faits et vérification individuelle
        facts = self._extract_facts(text)
        if facts:
            verification_results = []
            for fact in facts[:3]:  # Limiter à 3 faits pour éviter trop de requêtes
                result = self._check_fact(fact, text)
                verification_results.append(result)
            
            verified_count = sum(1 for r in verification_results if r.get('verified') is True)
            false_count = sum(1 for r in verification_results if r.get('verified') is False)
            total_count = len(verification_results)
            
            if false_count > verified_count:
                verified = False
                confidence = min(0.9, 0.5 + (false_count / total_count) * 0.3)
            elif verified_count > 0:
                verified = True
                confidence = min(0.9, 0.5 + (verified_count / total_count) * 0.3)
            else:
                verified = None
                confidence = 0.3
            
            return {
                "verified": verified,
                "confidence": float(confidence),
                "facts_checked": len(facts),
                "results": verification_results,
                "method": "fact_extraction"
            }
        
        return {
            "verified": None,
            "confidence": 0.3,
            "sources": [],
            "method": "no_results"
        }
    
    def _extract_facts(self, text: str) -> List[str]:
        """
        Extrait les faits vérifiables du texte
        """
        facts = []
        text_lower = text.lower()
        
        # Patterns pour extraire des affirmations factuelles
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(est|is|a été|has been)\s+(le|la|un|une|président|president|premier ministre)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(est mort|is dead|décédé|passed away)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(a|has)\s+(gagné|won|élu|elected)',
            r'(le|la)\s+([A-Z][a-z]+)\s+(est|is)\s+(vrai|true|faux|false)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fact = match.group(0).strip()
                if len(fact) > 10 and len(fact) < 200:
                    facts.append(fact)
        
        # Si aucun pattern ne correspond, prendre les phrases principales
        if not facts:
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                # Phrases courtes avec noms propres ou chiffres
                if (len(sentence) > 15 and len(sentence) < 150 and 
                    (re.search(r'[A-Z][a-z]+', sentence) or re.search(r'\d+', sentence))):
                    facts.append(sentence)
        
        return facts[:5]  # Limiter à 5 faits
    
    def _search_web(self, text: str) -> Dict:
        """
        Recherche sur Internet pour vérifier l'information
        Utilise plusieurs requêtes pour maximiser les résultats
        """
        all_results = []
        all_sources = []
        
        # Plusieurs requêtes de recherche pour améliorer les résultats
        search_queries = [
            f'"{text}"',
            f'{text} vérification',
            f'{text} fact-check',
            f'{text} vrai ou faux'
        ]
        
        for query in search_queries[:2]:  # Limiter à 2 requêtes pour éviter trop de requêtes
            try:
                search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
                response = self.session.get(search_url, timeout=8)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extraire les résultats (plusieurs sélecteurs possibles)
                    for result in soup.find_all('a', class_='result__a', limit=10):
                        title = result.get_text(strip=True)
                        href = result.get('href', '')
                        if title and href and title not in [r['title'] for r in all_results]:
                            all_results.append({"title": title, "url": href})
                    
                    # Aussi chercher dans d'autres formats de résultats
                    for link in soup.find_all('a', href=True):
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        if title and len(title) > 10 and 'duckduckgo.com' not in href:
                            if title not in [r['title'] for r in all_results]:
                                all_results.append({"title": title, "url": href})
                
            except Exception as e:
                logger.warning(f"Erreur recherche web pour '{query}': {e}")
        
        # Analyser les titres et URLs pour trouver des sources fiables
        source_keywords = [
            'snopes', 'factcheck', 'lemonde', 'franceinfo', 'france 24',
            'bbc', 'reuters', 'ap news', 'the guardian', 'wikipedia',
            'wikipédia', 'encyclopédie', 'biographie', 'biography'
        ]
        
        for result in all_results:
            title_lower = result['title'].lower()
            url_lower = result['url'].lower()
            for keyword in source_keywords:
                if keyword in title_lower or keyword in url_lower:
                    if result not in all_sources:
                        all_sources.append(result)
                    break
        
        return {
            "query": text,
            "results": all_results[:15],  # Limiter à 15 résultats
            "sources": all_sources,
            "results_count": len(all_results),
            "sources_found": len(all_sources)
        }
    
    def _analyze_search_results(self, text: str, search_result: Dict) -> Dict:
        """
        Analyse les résultats de recherche pour déterminer si l'info est vraie ou fausse
        """
        text_lower = text.lower()
        results = search_result.get("results", [])
        sources = search_result.get("sources", [])
        
        # Mots-clés indiquant que l'info est VRAIE
        true_keywords = [
            'vrai', 'true', 'correct', 'confirmé', 'confirmed', 'vérifié', 'verified',
            'officiel', 'official', 'source fiable'
        ]
        
        # Mots-clés indiquant que l'info est FAUSSE
        false_keywords = [
            'faux', 'false', 'fake', 'hoax', 'canular', 'rumeur', 'rumor',
            'démenti', 'debunked', 'démythifié', 'non vérifié'
        ]
        
        true_count = 0
        false_count = 0
        neutral_count = 0
        
        # Analyser les titres des résultats
        for result in results:
            title_lower = result.get('title', '').lower()
            url_lower = result.get('url', '').lower()
            
            # Vérifier si le titre contient des mots-clés
            has_true = any(kw in title_lower for kw in true_keywords)
            has_false = any(kw in title_lower for kw in false_keywords)
            
            if has_false:
                false_count += 1
            elif has_true:
                true_count += 1
            else:
                neutral_count += 1
        
        # Si on a des sources fiables, leur donner plus de poids
        if sources:
            for source in sources:
                title_lower = source.get('title', '').lower()
                has_false = any(kw in title_lower for kw in false_keywords)
                has_true = any(kw in title_lower for kw in true_keywords)
                
                if has_false:
                    false_count += 2  # Plus de poids pour les sources fiables
                elif has_true:
                    true_count += 2
        
        # Déterminer le verdict
        total_signals = true_count + false_count
        if total_signals == 0:
            verified = None
            confidence = 0.3
        elif false_count > true_count * 1.5:
            verified = False
            confidence = min(0.9, 0.5 + (false_count / max(total_signals, 1)) * 0.4)
        elif true_count > false_count * 1.5:
            verified = True
            confidence = min(0.9, 0.5 + (true_count / max(total_signals, 1)) * 0.4)
        else:
            verified = None  # Conflit ou pas assez d'info
            confidence = 0.4
        
        return {
            "verified": verified,
            "confidence": float(confidence),
            "true_signals": true_count,
            "false_signals": false_count
        }
    
    def _check_fact(self, fact: str, original_text: str) -> Dict:
        """
        Vérifie un fait spécifique en cherchant sur le web
        """
        search_result = self._search_web(fact)
        if search_result.get("sources_found", 0) > 0:
            analysis = self._analyze_search_results(fact, search_result)
            return {
                "fact": fact,
                "verified": analysis.get("verified"),
                "confidence": analysis.get("confidence", 0.5),
                "method": "web_search",
                "sources_found": search_result.get("sources_found", 0)
            }
        
        return {
            "fact": fact,
            "verified": None,
            "confidence": 0.3,
            "method": "no_results",
            "sources_found": 0
        }
    
    def check_against_known_facts(self, text: str) -> Dict:
        """
        Vérifie contre une base de faits connus (exemples)
        """
        text_lower = text.lower()
        
        # Base de faits connus (exemples)
        known_facts = {
            # Présidents actuels
            "emmanuel macron": {"is_president": True, "country": "France", "since": 2017, "verified": True},
            "joe biden": {"is_president": True, "country": "USA", "since": 2021, "verified": True},
            
            # Personnalités et nationalités
            "messi": {"nationality": "argentin", "verified": True},
            "messi est argentin": {"verified": True, "correct": True},
            "messi est argentinien": {"verified": True, "correct": True},
            "messi est français": {"verified": False, "correct": False},
            
            # Fausses nouvelles connues
            "presidante": {"is_correct": False, "correct": "présidente", "verified": False},
        }
        
        matches = []
        verified_as_true = False
        verified_as_false = False
        
        # Vérifier les correspondances exactes et partielles
        for key, fact_data in known_facts.items():
            key_lower = key.lower()
            # Correspondance exacte ou partielle (le fait peut être dans le texte)
            if key_lower in text_lower or text_lower in key_lower:
                matches.append({
                    "fact": key,
                    "data": fact_data,
                    "verified": fact_data.get("verified", True)
                })
                if fact_data.get("verified") is True and fact_data.get("correct", True):
                    verified_as_true = True
                elif fact_data.get("verified") is False or fact_data.get("correct") is False:
                    verified_as_false = True
        
        # Vérification spéciale pour "Messi est argentin/argentinien"
        if "messi" in text_lower and ("argentin" in text_lower or "argentine" in text_lower):
            verified_as_true = True
            matches.append({
                "fact": "messi est argentin",
                "data": {"verified": True, "correct": True},
                "verified": True
            })
        
        return {
            "matches": matches,
            "count": len(matches),
            "verified_as_true": verified_as_true,
            "verified_as_false": verified_as_false
        }

