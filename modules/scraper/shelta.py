"""Shelta scraper handler."""

from typing import Dict, List
from .base import BaseScraper

class SheltaHandler(BaseScraper):
    """Scraper für shelta.tasso.net"""
    
    async def extract_detail(self, page) -> Dict:
        title_el = await page.query_selector("h1, h2")
        title = await title_el.inner_text() if title_el else ""
        
        desc_el = await page.query_selector("div.description, div.content")
        description = await desc_el.inner_text() if desc_el else ""
        
        age = None
        import re
        age_match = re.search(r'(\d+)\s*Jahr', description)
        if age_match:
            age = int(age_match.group(1))
        
        return {
            "title": title.strip(),
            "description": description.strip(),
            "age": age,
            "extracted_at": __import__('datetime').datetime.now().isoformat()
        }
    

