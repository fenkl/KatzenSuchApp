"""TierheimHelden scraper handler."""

from typing import Dict, List
from .base import BaseScraper

class TierheimHeldenHandler(BaseScraper):
    """Scraper für tierheimhelden.de"""
    
    async def extract_detail(self, page) -> Dict:
        title_el = await page.query_selector("h1")
        title = await title_el.inner_text() if title_el else ""
        
        desc_el = await page.query_selector("div.description, div.detail")
        description = await desc_el.inner_text() if desc_el else ""
        
        # Extract age, location, etc.
        age = None
        import re
        age_match = re.search(r'(\d+)\s*Jahr(?:e)?', description)
        if age_match:
            age = int(age_match.group(1))
        
        return {
            "title": title.strip(),
            "description": description.strip(),
            "age": age,
            "extracted_at": __import__('datetime').datetime.now().isoformat()
        }
    

