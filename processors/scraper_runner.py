from datetime import datetime
import time
from scrapers.scraper_manager import get_scraper, SCRAPER_MAP
from utils.database import Database
from utils.http_helper import fetch_page, extract_og_image
from utils.freshness_filter import FreshnessFilter
from utils.logger import log_info, log_error, log_success, log_warning
from bs4 import BeautifulSoup

class ScraperRunner:
    def __init__(self):
        self.db = Database()
        self.freshness_filter = FreshnessFilter(max_age_hours=48)
        
        # API source names that don't need HTML fetching
        self.api_sources = ["GNews", "YouTube", "NewsAPI", "Google Trends"]
        
        # Stats for the current run
        self.stats = {
            'total_articles': 0,
            'saved_articles': 0,
            'skipped_no_image': 0,
            'skipped_other': 0,
            'errors': 0
        }
    
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
                    headline = article.get("headline", "")
                    summary = article.get("summary", "")
                    url = article.get("url", "")
                    # First try to get the initial image from the article data
                    image_url = article.get("image", "")
                    
                    # If no image found in initial data, try to fetch the article page for OpenGraph image
                    if not image_url or str(image_url).strip() == "":
                        log_warning(f"No initial image found for article: {headline[:50]}...")
                        if url and not any(x in url.lower() for x in ['#', 'mailto:', 'tel:']):
                            try:
                                log_info(f"Fetching article page for image: {url}")
                                html = fetch_page(url)
                                if html:
                                    # First try OpenGraph image
                                    og_image = extract_og_image(html)
                                    if og_image and not any(x in og_image.lower() for x in ['logo', 'icon']):
                                        image_url = og_image
                                        log_info(f"Found OpenGraph image: {og_image}")
                                    else:
                                        # If no OpenGraph, try to find a suitable image in the article
                                        soup = BeautifulSoup(html, 'lxml')
                                        article_img = soup.select_one('article img[src*="."]') or \
                                                    soup.select_one('.article-content img[src*="."]') or \
                                                    soup.select_one('main img[src*="."]')
                                        
                                        if article_img:
                                            src = article_img.get('src') or article_img.get('data-src', '')
                                            if src and not any(x in src.lower() for x in ['logo', 'icon']):
                                                # Make relative URLs absolute
                                                if src.startswith('//'):
                                                    src = 'https:' + src
                                                elif src.startswith('/'):
                                                    from urllib.parse import urlparse
                                                    parsed_uri = urlparse(url)
                                                    src = f"{parsed_uri.scheme}://{parsed_uri.netloc}{src}"
                                                image_url = src
                                                log_info(f"Found article image: {image_url}")
                                        
                                        if not image_url:
                                            log_warning(f"No suitable image found for {url}")
                                            self.stats['skipped_no_image'] += 1
                                            continue
                                else:
                                    log_warning(f"Failed to fetch article page: {url}")
                                    self.stats['skipped_other'] += 1
                                    continue
                            except Exception as e:
                                log_error(f"Error processing article page: {e}")
                                self.stats['errors'] += 1
                                continue
                        else:
                            log_warning(f"Invalid or missing URL for article: {headline[:50]}...")
                            self.stats['skipped_other'] += 1
                            continue
                    else:
                        log_info(f"Found initial image: {image_url}")

                    success = self.db.add_content(
                        source_id=source["id"],
                        headline=headline,
                        summary=summary,
                        original_url=url,
                        image_url=image_url,
                        source_language=article.get("language", source["language"]),
                        country=article.get("country", source["country"]),
                        country_code=article.get("country_code", source["country_code"]),
                        niche=article.get("niche", source["niche"])
                    )
                    if success:
                        saved += 1
                except Exception as e:
                    # Log specific errors here to debug DB issues
                    import traceback
                    error_details = traceback.format_exc()
                    log_error(f"Error saving article from {source_name}: {e}\n{error_details}")
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
        self.stats = {
            'total_articles': 0,
            'saved_articles': 0,
            'skipped_no_image': 0,
            'skipped_other': 0,
            'errors': 0
        }
        
        sources = self.db.get_active_sources()
        log_info(f"Found {len(sources)} active sources")
        
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
                self.stats['total_articles'] += saved
                if saved > 0:
                    successful += 1
                else:
                    failed += 1
                # Add a small delay between sources to be nice to the servers
                time.sleep(2)
            except Exception as e:
                log_error(f"Error running {source.get('name', 'Unknown')}: {e}")
                failed += 1
        
        # Log final stats
        log_info("\n=== Scraper Run Statistics ===")
        log_info(f"Total articles processed: {self.stats['total_articles']}")
        log_info(f"Articles saved: {self.stats['saved_articles']}")
        log_info(f"Skipped (no image): {self.stats['skipped_no_image']}")
        log_info(f"Skipped (other reasons): {self.stats['skipped_other']}")
        log_info(f"Errors: {self.stats['errors']}")
        log_info("============================\n")
        
        log_info(f"Scraper run complete: {successful} successful, {failed} failed, {self.db.get_pending_content_count()} articles saved")
        
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