from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from utils.http_helper import fetch_page, extract_og_image
from utils.database import Database
from utils.logger import log_info, log_error, log_scrape, log_warning
from utils.image_finder import get_stock_image

class GenericScraper(ABC):
    """A generic scraper that can be used as a fallback for any source"""
    def __init__(self, source_id, name, url, country, country_code, language, niche):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.country = country
        self.country_code = country_code
        self.language = language
        self.niche = niche
    
    def parse_articles(self, html):
        """
        Parse the HTML to extract article information.
        This is a generic implementation that can be overridden by specific scrapers.
        """
        soup = self.get_soup(html)
        articles = []
        
        # Look for common article selectors
        article_selectors = [
            'article',
            '.article',
            '.post',
            '.entry',
            '.news-item',
            'div[itemprop="articleBody"]',
            'div.article-body',
            'div.post-content'
        ]
        
        for selector in article_selectors:
            articles = soup.select(selector)
            if articles:
                break
                
        if not articles:
            # If no articles found with specific selectors, try to find any links with text
            links = soup.select('a')
            articles = [link for link in links if len(link.get_text(strip=True)) > 50]
            
        return articles or []

    def scrape(self):
        """Default implementation of the scrape method"""
        log_info(f"Scraping {self.name} (using generic scraper)...")
        html = fetch_page(self.url)
        if not html:
            log_error(f"Failed to fetch {self.name}")
            return []
            
        articles = self.parse_articles(html)
        return articles

class BaseScraper(GenericScraper):
    def __init__(self, source_id, name, url, country, country_code, language, niche):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.country = country
        self.country_code = country_code
        self.language = language
        self.niche = niche
    
    @abstractmethod
    def parse_articles(self, html):
        pass
    
    def scrape(self):
        log_info(f"Scraping {self.name}...")
        html = fetch_page(self.url)
        if not html:
            log_error(f"Failed to fetch {self.name}")
            return []
        
        articles = self.parse_articles(html)
        saved_count = 0
        
        for article in articles:
            if not article.get("headline"):
                continue
            
            # Check if exists before fetching body to save requests
            if db.content_exists(article.get("headline", "")):
                continue

            # Store the initial image URL before any processing
            initial_image = article.get("image", "")
            
            # Fetch full article details (text + high-res image)
            full_text, og_image = self.fetch_full_details(article.get("url", ""))
            
            # Use full text if found, otherwise fall back to excerpt
            final_summary = full_text if full_text and len(full_text) > 200 else article.get("summary", "")
            
            # Use OG image if list-page image is missing/broken
            final_image = initial_image  # Start with the initial image
            if (not final_image or "base64" in final_image) and og_image:
                final_image = og_image
            
            # LAST RESORT: Stock Image Fallback - Use article-specific stock image
            if not final_image or "base64" in final_image or any(domain in str(final_image).lower() for domain in ["cdn.tuko.co.ke", "placeholder", "default", "logo", "icon"]):
                # Create a unique query using headline and URL to ensure different images
                unique_query = f"{article.get('headline', '')} {article.get('url', '')}"
                stock_img = get_stock_image(unique_query)
                if stock_img:
                    final_image = stock_img
                    log_info(f"Using unique stock image for: {article.get('headline')[:20]}...")
                else:
                    log_warning(f"No suitable image found for: {article.get('headline')[:20]}...")
                    self.mark_article_skipped(article.get("url"), "no_suitable_image")
                    continue  # Skip this article if no image is found

            result = db.add_content(
                source_id=self.source_id,
                headline=article.get("headline", ""),
                summary=final_summary, 
                original_url=article.get("url", ""),
                image_url=final_image,
                initial_image_url=initial_image,  # Pass the initial image URL
                source_language=self.language,
                country=self.country,
                country_code=self.country_code,
                niche=self.niche
            )
            
            if result:
                saved_count += 1
                from time import sleep
                sleep(2) 
        
        db.update_source_scraped(self.source_id)
        log_scrape(self.name, saved_count)
        return saved_count

    def mark_article_skipped(self, url, reason):
        """Mark an article as skipped with a reason"""
        log_warning(f"Article skipped - {reason}: {url}")

    def fetch_full_details(self, url):
        """Fetches full text and og:image from the article URL."""
        if not url:
            return "", ""
        try:
            html = fetch_page(url)
            if not html:
                return "", ""
            soup = self.get_soup(html)
            
            # 1. Extract Body Text
            body_container = soup.select_one("article, div.article-body, div.post-content, div.entry-content, div#content, div.content")
            if body_container:
                paragraphs = body_container.find_all("p")
            else:
                paragraphs = soup.find_all("p")
            
            text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40]
            body_text = "\n\n".join(text_blocks)
            
            # 2. Extract OpenGraph Image (High Quality)
            og_image = extract_og_image(soup)
            if og_image:
                og_image = self.make_absolute_url(og_image)
            
            return body_text, og_image
            
        except Exception as e:
            log_warning(f"Could not fetch details for {url}: {e}")
            return "", ""
    
    def get_soup(self, html):
        return BeautifulSoup(html, "lxml")
    
    def clean_text(self, text):
        if not text:
            return ""
        return " ".join(text.strip().split())
    
    def make_absolute_url(self, relative_url):
        if not relative_url:
            return ""
        if relative_url.startswith("http"):
            return relative_url
        if relative_url.startswith("//"):
            return "https:" + relative_url
        if relative_url.startswith("/"):
            base = self.url.rstrip("/")
            return base + relative_url
        return self.url.rstrip("/") + "/" + relative_url