import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser

class FreshnessFilter:
    """Filter articles to ensure they are recent (within last 48 hours)"""
    
    def __init__(self, max_age_hours=48):
        self.max_age_hours = max_age_hours
        self.cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
    
    def is_fresh(self, article):
        """Check if article is within the freshness window"""
        
        # Check published_at field (from APIs)
        published_at = article.get("published_at", "")
        if published_at:
            try:
                pub_date = date_parser.parse(published_at)
                if pub_date.tzinfo:
                    pub_date = pub_date.replace(tzinfo=None)
                return pub_date >= self.cutoff_time
            except:
                pass
        
        # Check URL for date patterns
        url = article.get("url", "")
        date_from_url = self.extract_date_from_url(url)
        if date_from_url:
            return date_from_url >= self.cutoff_time.date()
        
        # Check headline/summary for date indicators
        headline = article.get("headline", "").lower()
        summary = article.get("summary", "").lower()
        text = headline + " " + summary
        
        fresh_indicators = ["today", "aujourd'hui", "breaking", "just in", "vient de", "ce matin", "this morning"]
        if any(indicator in text for indicator in fresh_indicators):
            return True
        
        stale_indicators = ["last year", "l'an dernier", "2023", "2022", "2021", "2020"]
        if any(indicator in text for indicator in stale_indicators):
            return False
        
        return True
    
    def extract_date_from_url(self, url):
        """Extract date from URL patterns"""
        patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{4})-(\d{2})-(\d{2})/',
            r'/(\d{4})(\d{2})(\d{2})/',
            r'-(\d{4})(\d{2})(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                        return datetime(year, month, day).date()
                except:
                    pass
        
        return None
    
    def filter_articles(self, articles, verbose=False):
        """Filter list of articles to only fresh ones"""
        fresh = []
        stale = 0
        
        for article in articles:
            if self.is_fresh(article):
                fresh.append(article)
            else:
                stale += 1
        
        if verbose and stale > 0:
            print(f"Filtered out {stale} stale articles, kept {len(fresh)} fresh")
        
        return fresh


if __name__ == "__main__":
    filter = FreshnessFilter(max_age_hours=48)
    
    test_articles = [
        {"headline": "Breaking news today", "url": "https://example.com/2025/12/28/article", "published_at": ""},
        {"headline": "Old news from 2023", "url": "https://example.com/2023/01/15/article", "published_at": ""},
        {"headline": "Recent update", "url": "https://example.com/article", "published_at": "2025-12-28T10:00:00Z"},
        {"headline": "Something happened", "url": "https://example.com/old", "published_at": "2025-01-01T10:00:00Z"},
    ]
    
    print("Testing Freshness Filter")
    print("="*50)
    print(f"Cutoff time: {filter.cutoff_time}")
    
    for article in test_articles:
        is_fresh = filter.is_fresh(article)
        status = "FRESH" if is_fresh else "STALE"
        print(f"\n{status}: {article['headline'][:40]}...")
        print(f"  URL date: {filter.extract_date_from_url(article['url'])}")
        print(f"  Published: {article.get('published_at', 'N/A')}")