from datetime import datetime
from scrapers.scraper_manager import get_scraper, SCRAPER_MAP
from utils.database import Database
from utils.http_helper import fetch_page
from utils.freshness_filter import FreshnessFilter
from utils.logger import log_info, log_error, log_success, log_warning

class ScraperRunner:
    def __init__(self):
        self.db = Database()
        self.freshness_filter = FreshnessFilter(max_age_hours=48)
        
        # API source names that don't need HTML fetching
        self.api_sources = ["GNews", "YouTube", "NewsAPI", "Google Trends"]
    
    def run_single_source(self, source):
        """Run scraper for a single source"""
        try:
            source_name = source.get("name", "Unknown")
            
            # Skip Reddit if still in database
            if source_name == "Reddit":
                return 0
            
            scraper = get_scraper(source)
            
            # For API scrapers, call parse_articles without HTML
            if source_name in self.api_sources or source.get("source_type") == "api":
                try:
                    articles = scraper.parse_articles(None)
                except Exception as e:
                    log_warning(f"API scraper {source_name} failed: {e}")
                    return 0
            else:
                # Web scrapers need HTML
                html = fetch_page(source["url"])
                if not html:
                    log_warning(f"Failed to fetch {source_name}")
                    return 0
                articles = scraper.parse_articles(html)
            
            if not articles:
                return 0
            
            # Apply freshness filter
            fresh_articles = self.freshness_filter.filter_articles(articles)
            
            if not fresh_articles:
                return 0
            
            # Save to database
            saved = 0
            for article in fresh_articles:
                try:
                    success = self.db.add_content(
                        source_id=source["id"],
                        headline=article.get("headline", ""),
                        summary=article.get("summary", ""),
                        original_url=article.get("url", ""),
                        image_url=article.get("image", ""),
                        source_language=article.get("language", source["language"]),
                        country=article.get("country", source["country"]),
                        country_code=article.get("country_code", source["country_code"]),
                        niche=article.get("niche", source["niche"])
                    )
                    if success:
                        saved += 1
                except Exception as e:
                    continue
            
            if saved > 0:
                log_success(f"{source_name}: Saved {saved} articles")
            
            # Update last_scraped timestamp
            self.db.update_source_scraped(source["id"])
            
            return saved
            
        except Exception as e:
            log_error(f"Error scraping {source.get('name', 'Unknown')}: {e}")
            return 0
    
    def run_all(self):
        """Run all active scrapers"""
        log_info("Starting scraper run...")
        
        sources = self.db.get_active_sources()
        
        if not sources:
            log_warning("No active sources found")
            return 0
        
        log_info(f"Running {len(sources)} scrapers...")
        
        total_saved = 0
        successful = 0
        failed = 0
        
        for source in sources:
            try:
                saved = self.run_single_source(source)
                if saved > 0:
                    successful += 1
                    total_saved += saved
                else:
                    failed += 1
            except Exception as e:
                log_error(f"Error with {source.get('name', 'Unknown')}: {e}")
                failed += 1
        
        log_info(f"Scraper run complete: {successful} successful, {failed} failed, {total_saved} articles saved")
        
        return total_saved
    
    def run_priority_sources(self):
        """Run only high-priority sources (for quick updates)"""
        log_info("Running priority sources...")
        
        sources = self.db.get_active_sources()
        priority_sources = [s for s in sources if s.get("priority", 2) == 1]
        
        total_saved = 0
        for source in priority_sources:
            saved = self.run_single_source(source)
            total_saved += saved
        
        return total_saved

scraper_runner = ScraperRunner()