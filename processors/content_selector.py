from utils.database import Database

db = Database()
from utils.logger import log_info, log_warning
from config.settings import LANGUAGE_SPLIT
import random

class ContentSelector:
    def __init__(self):
        self.target_french = LANGUAGE_SPLIT["french"]
        self.target_english = LANGUAGE_SPLIT["english"]
    
    def get_next_language(self):
        ratio = db.get_language_ratio(hours=24)
        
        if ratio["total"] == 0:
            return "french"  # Start with french (majority audience)
        
        current_french_pct = ratio["french_pct"] / 100
        
        # If french is below target, post french
        if current_french_pct < self.target_french:
            return "french"
        else:
            return "english"
    
    def select_content(self, schedule_slot=None):
        # Determine language needed
        output_language = self.get_next_language()
        
        # Get target country and niche from schedule if provided
        target_country = None
        target_niche = None
        
        if schedule_slot:
            target_country = schedule_slot.get("target_country")
            target_niche = schedule_slot.get("target_niche")
            # Schedule might override language
            if schedule_slot.get("target_language"):
                output_language = schedule_slot["target_language"]
        
        # Try to find content matching criteria
        country_code = self._get_country_code(target_country)
        
        # First try: exact match
        content = db.get_pending_content(
            country_code=country_code,
            niche=target_niche,
            limit=5
        )
        
        # Second try: just country
        if not content and country_code:
            content = db.get_pending_content(
                country_code=country_code,
                limit=5
            )
        
        # Third try: just niche
        if not content and target_niche:
            content = db.get_pending_content(
                niche=target_niche,
                limit=5
            )
        
        # Fourth try: any pending content
        if not content:
            content = db.get_pending_content(limit=10)
        
        if not content:
            log_warning("No pending content available")
            return None, None
        
        # Pick one randomly from top results
        selected = random.choice(content[:min(3, len(content))])
        
        log_info(f"Selected: [{selected['country']}] {selected['headline'][:50]}...")
        log_info(f"Output language: {output_language}")
        
        return selected, output_language
    
    def _get_country_code(self, country_name):
        if not country_name:
            return None
        
        mapping = {
            "Burundi": "BI",
            "DRC": "CD",
            "Ivory Coast": "CI",
            "Kenya": "KE",
            "Burkina Faso": "BF",
            "Mali": "ML",
            "Guinea": "GN",
            "Nigeria": "NG",
            "South Africa": "ZA",
            "Ghana": "GH",
            "Senegal": "SN",
            "Cameroon": "CM",
            "Morocco": "MA",
            "Ethiopia": "ET",
            "Rwanda": "RW",
            "Pan-African": "AF",
        }
        
        return mapping.get(country_name)

content_selector = ContentSelector()

# Updated 12/29/2025 00:17:30
