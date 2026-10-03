"""LLM Filter Service with Tailscale Client and Cache for KatzenSuchApp."""

import hashlib
import json
import asyncio
import aiohttp
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from classes.Cconfig import Config
from modules.Mhandle_log import get_logger
from modules.db_utils import get_llm_classification, cache_llm_classification

log = get_logger(__name__)
config = Config()


@dataclass
class LLMFilterResponse:
    """Response from LLM filter."""
    is_match: bool
    confidence: float
    reasoning: str
    age_ok: bool
    einzelgaenger_ok: bool
    freigang_ok: bool
    age_unsicher: bool
    einzelgaenger_unsicher: bool
    freigang_unsicher: bool


class LLMFilterService:
    """Service for filtering listings using LLM via Tailscale."""
    
    def __init__(self):
        self.ollama_url = config.ollama_url
        self.ollama_model = config.ollama_model
        self.ollama_timeout = config.ollama_timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.ollama_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _get_url_hash(self, url: str) -> str:
        """Generate hash for URL caching."""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def _get_cached_classification(self, url: str) -> Optional[Dict]:
        """Get cached LLM classification from DB."""
        classification = get_llm_classification(url)
        if classification:
            log.debug(f"Cache hit for {url}")
            return classification
        return None
    
    def _cache_classification(self, url: str, platform: str, result: Dict):
        """Cache LLM classification in DB."""
        cache_llm_classification(url, platform, result)
    
    def _build_prompt(self, listing: Dict) -> str:
        """Build prompt for LLM classification."""
        title = listing.get("title", "")
        description = listing.get("description", "")
        
        prompt = f"""Du bist ein Experte für Katzenvermittlung.

Bewerte die folgende Katzenanzeige gegen diese Kriterien:
- Alter zwischen 2 und 8 Jahren
- Einzelgänger geeignet (katzenverträglich oder Einzelkatze)
- Kein Freigang nötig (Wohnungskatze oder kein Freigang gewünscht)

Anzeige:
Titel: {title}
Beschreibung: {description}

Analysiere und antworte AUSSCHLIESSLICH als JSON mit diesem Schema:
{{
  "is_match": boolean,
  "confidence": float (0-1),
  "reasoning": string,
  "age_ok": boolean,
  "einzelgaenger_ok": boolean,
  "freigang_ok": boolean,
  "age_unsicher": boolean,
  "einzelgaenger_unsicher": boolean,
  "freigang_unsicher": boolean
}}

Wichtig: Sei konservativ bei Unsicherheiten. Setze unsicher auf true wenn Info fehlt.
"""
        return prompt
    
    async def _query_ollama(self, prompt: str) -> Optional[Dict]:
        """Query Ollama API via Tailscale."""
        try:
            session = await self._get_session()
            
            payload = {
                "model": self.ollama_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "format": "json",
                "options": {
                    "temperature": 0.1
                }
            }
            
            async with session.post(
                self.ollama_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    log.error(f"Ollama API error: {response.status}")
                    return None
                
                data = await response.json()
                
                # Extract response content
                message = data.get("message", {})
                content = message.get("content", "")
                
                # Parse JSON response
                try:
                    result = json.loads(content)
                    return result
                except json.JSONDecodeError as e:
                    log.error(f"Failed to parse Ollama JSON: {e}, content: {content}")
                    return None
                    
        except asyncio.TimeoutError:
            log.error(f"Ollama request timeout after {self.ollama_timeout}s")
            return None
        except Exception as e:
            log.error(f"Ollama query error: {e}")
            return None
    
    async def classify_listing(self, url: str, listing: Dict, platform: str) -> LLMFilterResponse:
        """Classify a listing using LLM with caching."""
        # Check cache first
        cached = self._get_cached_classification(url)
        if cached:
            return LLMFilterResponse(**cached)
        
        # Pre-filter check to avoid LLM calls
        if not self._pre_filter_pass(listing):
            log.debug(f"Pre-filter rejected {url}")
            result = {
                "is_match": False,
                "confidence": 0.9,
                "reasoning": "Pre-filter rejected",
                "age_ok": False,
                "einzelgaenger_ok": False,
                "freigang_ok": False,
                "age_unsicher": True,
                "einzelgaenger_unsicher": True,
                "freigang_unsicher": True
            }
            self._cache_classification(url, platform, result)
            return LLMFilterResponse(**result)
        
        # Query LLM
        prompt = self._build_prompt(listing)
        llm_result = await self._query_ollama(prompt)
        
        if llm_result:
            # Cache result
            self._cache_classification(url, platform, llm_result)
            return LLMFilterResponse(**llm_result)
        else:
            # Fallback: assume no match on error
            log.warning(f"LLM classification failed for {url}, using fallback")
            fallback = {
                "is_match": False,
                "confidence": 0.0,
                "reasoning": "LLM service unavailable",
                "age_ok": False,
                "einzelgaenger_ok": False,
                "freigang_ok": False,
                "age_unsicher": True,
                "einzelgaenger_unsicher": True,
                "freigang_unsicher": True
            }
            self._cache_classification(url, platform, fallback)
            return LLMFilterResponse(**fallback)
    
    def _pre_filter_pass(self, listing: Dict) -> bool:
        """Quick pre-filter to avoid unnecessary LLM calls."""
        description = (listing.get("description", "") + " " + listing.get("title", "")).lower()
        
        # Very basic checks
        # Age mention
        import re
        age_match = re.search(r'(\d+)\s*jahr', description)
        if age_match:
            age = int(age_match.group(1))
            if age < 2 or age > 8:
                return False
        
        # If no age info or age is ok, proceed to LLM
        return True
    
    async def filter_listings(self, listings: List[Dict], platform: str) -> List[Dict]:
        """Filter multiple listings using LLM."""
        filtered = []
        
        for listing in listings:
            url = listing.get("url")
            if not url:
                continue
            
            result = await self.classify_listing(url, listing, platform)
            
            if result.is_match and result.confidence >= 0.7:
                listing["llm_classification"] = {
                    "is_match": result.is_match,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "age_ok": result.age_ok,
                    "einzelgaenger_ok": result.einzelgaenger_ok,
                    "freigang_ok": result.freigang_ok,
                }
                filtered.append(listing)
                log.info(f"LLM accepted {url} with confidence {result.confidence}")
            else:
                log.debug(f"LLM rejected {url}: {result.reasoning}")
        
        return filtered
    
    async def close(self):
        """Close session."""
        if self.session and not self.session.closed:
            await self.session.close()
            log.info("LLM Filter Service session closed")


# Singleton instance
llm_filter_service = LLMFilterService()
