from datetime import datetime
import time
from scrapers.scraper_manager import get_scraper, SCRAPER_MAP
from utils.database import Database
from utils.http_helper import fetch_page, extract_og_image
from utils.freshness_filter import FreshnessFilter
from utils.logger import log_info, log_error, log_success, log_warning
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class ScraperRunner:
    def __init__(self):
        try:
            self.db = Database()
            self.freshness_filter = FreshnessFilter(max_age_hours=48)
            self.api_sources = ["GNews", "YouTube", "NewsAPI", "Google Trends"]
            self.stats = {
                'total_articles': 0,
                'saved_articles': 0,
                'skipped_no_image': 0,
                'skipped_other': 0,
                'errors': 0
            }
            log_info("ScraperRunner initialized successfully")
        except Exception as e:
            log_error(f"Failed to initialize ScraperRunner: {e}")
            raise

    def _process_image_url(self, url, article_url):
        """Helper to process and validate image URLs"""
        if not url:
            return None
            
        try:
            # Make relative URLs absolute
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                parsed_uri = urlparse(article_url)
                url = f"{parsed_uri.scheme}://{parsed_uri.netloc}{url}"
                
            # Skip placeholder or invalid images
            if any(x in url.lower() for x in ['logo', 'icon', 'placeholder', 'sprite']):
                return None
                
            return url
        except Exception as e:
            log_error(f"Error processing image URL {url}: {e}")
            return None

    def _extract_article_image(self, soup, article_url):
        """Extract image from article content"""
        try:
            # Try common image containers
            selectors = [
                'article img[src*="."]',
                '.article-content img[src*="."]',
                'main img[src*="."]',
                'figure img[src*="."]',
                '.post-thumbnail img[src*="."]'
            ]
            
            for selector in selectors:
                try:
                    img = soup.select_one(selector)
                    if img:
                        src = img.get('src') or img.get('data-src', '')
                        if src:
                            processed_url = self._process_image_url(src, article_url)
                            if processed_url:
                                return processed_url
                except Exception as e:
                    log_error(f"Error with selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            log_error(f"Error extracting article image: {e}")
            
        return None

    def _save_article(self, source, article, image_url):
        """Helper method to save article to database"""
        try:
            headline = article.get("headline", "").strip()
            summary = article.get("summary", "").strip()
            url = article.get("url", "").strip()
            
            if not all([headline, url]):
                log_warning("Skipping article - missing required fields (headline/URL)")
                self.stats['skipped_other'] += 1
                return False

            # Save to database
            success = self.db.add_content(
                source_id=source["id"],
                headline=headline,
                summary=summary,
                original_url=url,
                image_url=image_url,
                source_language=article.get("language", source.get("language", "en")),
                country=article.get("country", source.get("country", "")),
                country_code=article.get("country_code", source.get("country_code", "")),
                niche=article.get("niche", source.get("niche", "general"))
            )
            
            if success:
                self.stats['saved_articles'] += 1
                log_info(f"Saved article: {headline[:50]}...")
            else:
                log_warning(f"Failed to save article (possible duplicate): {headline[:50]}...")
                self.stats['skipped_other'] += 1
                
            return success
            
        except Exception as e:
            log_error(f"Error saving article: {e}")
            self.stats['errors'] += 1
            return False

    def run_single_source(self, source):
        """Run scraper for a single source"""
        source_name = source.get("name", "Unknown")
        log_info(f"Processing source: {source_name}")
        
        if source_name == "Reddit":
            return 0
            
        try:
            scraper = get_scraper(source)
            
            # Get articles
            if source_name in self.api_sources or source.get("source_type") == "api":
                try:
                    articles = scraper.parse_articles(None)
                except Exception as e:
                    log_warning(f"API scraper {source_name} failed: {e}")
                    return 0
            else:
                html = fetch_page(source["url"])
                if not html:
                    log_warning(f"Failed to fetch {source_name}")
                    return 0
                articles = scraper.parse_articles(html)
            
            if not articles:
                log_warning(f"No articles found for {source_name}")
                return 0
            
            # Apply freshness filter
            fresh_articles = self.freshness_filter.filter_articles(articles)
            log_info(f"Found {len(articles)} total articles, {len(fresh_articles)} fresh articles")
            
            if not fresh_articles:
                log_info(f"No fresh articles for {source_name}")
                return 0
             
            # Process and save articles
            saved = 0
            for article in fresh_articles:
                try:
                    headline = article.get("headline", "").strip()
                    url = article.get("url", "").strip()
                    
                    if not all([headline, url]):
                        log_warning("Skipping article - missing required fields (headline/URL)")
                        self.stats['skipped_other'] += 1
                        continue
                    
                    # Process image
                    image_url = article.get("image", "").strip()
                    if not image_url:
                        log_info(f"Fetching article page for image: {url[:100]}...")
                        try:
                            html = fetch_page(url)
                            if html:
                                # Try OpenGraph first
                                image_url = extract_og_image(html)
                                if not image_url:
                                    # Fall back to content image
                                    soup = BeautifulSoup(html, 'lxml')
                                    image_url = self._extract_article_image(soup, url)
                        except Exception as e:
                            log_error(f"Error fetching article page: {e}")
                    
                    if not image_url:
                        log_warning(f"Skipping article - no valid image found: {headline[:50]}...")
                        self.stats['skipped_no_image'] += 1
                        continue
                    
                    # Save the article
                    if self._save_article(source, article, image_url):
                        saved += 1
                        
                except Exception as e:
                    log_error(f"Error processing article: {e}")
                    self.stats['errors'] += 1
                    continue
            
            if saved > 0:
                log_success(f"{source_name}: Saved {saved} articles")
                try:
                    self.db.update_source_scraped(source["id"])
                except Exception as e:
                    log_error(f"Error updating last_scraped for {source_name}: {e}")
            
            return saved
            
        except Exception as e:
            log_error(f"Error in {source_name}: {e}")
            self.stats['errors'] += 1
            return 0

    def run_all(self):
        """Run all active scrapers"""
        start_time = time.time()
        log_info("Starting scraper run...")
        self.stats = {k: 0 for k in self.stats}
        
        try:
            sources = self.db.get_active_sources()
            if not sources:
                log_warning("No active sources found")
                return 0
                
            log_info(f"Found {len(sources)} active sources")
            total_saved = 0
            successful = 0
            failed = 0
            
            for source in sources:
                try:
                    saved = self.run_single_source(source)
                    if saved is not None:
                        successful += 1 if saved > 0 else 0
                        failed += 1 if saved == 0 else 0
                        total_saved += saved
                    time.sleep(2)  # Be nice to servers
                except Exception as e:
                    log_error(f"Error running source: {e}")
                    failed += 1
                    self.stats['errors'] += 1

            # Get pending count safely
            pending_content = self.db.get_pending_content()
            pending_count = len(pending_content) if pending_content else 0

            # Log final stats
            run_time = time.time() - start_time
            log_info("\n=== Scraper Run Summary ===")
            log_info(f"Total articles processed: {self.stats['saved_articles'] + self.stats['skipped_no_image'] + self.stats['skipped_other']}")
            log_info(f"Articles saved: {self.stats['saved_articles']}")
            log_info(f"Skipped - no image: {self.stats['skipped_no_image']}")
            log_info(f"Skipped - other reasons: {self.stats['skipped_other']}")
            log_info(f"Errors: {self.stats['errors']}")
            log_info(f"Run time: {run_time:.2f} seconds")
            log_info(f"Pending articles in queue: {pending_count}")
            log_info("===========================\n")
            
            return total_saved
            
        except Exception as e:
            log_error(f"Fatal error in scraper run: {e}")
            return 0

# Create a global instance of the ScraperRunner
scraper_runner = ScraperRunner()