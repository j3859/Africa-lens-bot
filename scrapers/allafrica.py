from scrapers.base_scraper import BaseScraper
import time
import re
import random
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class AllAfricaScraper(BaseScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://allafrica.com"
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        
    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://allafrica.com/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def clean_text(self, text):
        """Clean up text by removing extra whitespace and newlines"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text
        
    def make_absolute_url(self, url):
        """Convert relative URLs to absolute"""
        if not url:
            return ""
        if url.startswith(('http://', 'https://')):
            return url
        return urljoin(self.base_url, url)

    def parse_articles(self, html):
        """Parse articles from the AllAfrica homepage"""
        soup = self.get_soup(html)
        articles = []
        
        # Try multiple selectors to find article containers
        article_containers = []
        
        # Try different container selectors
        container_selectors = [
            'article.story', 
            'div.story', 
            'div.feed-article', 
            'div.story-item', 
            'div.item',
            'div.article',
            'div.article-card',
            'div.article-item',
            'div.article-wrapper',
            'div.news-item',
            'div.news-card',
            'div.news-wrapper',
            'div.post',
            'div.entry',
            'div.article-listing',
            'div.news-listing',
            'div.view-content div.views-row',
            'div.content div.node',
            'div.region-content article',
            'main article',
            'div#main-content article',
            'div#content article',
            'div#main article',
            'div#content-inner article',
            'div#main-inner article',
            'section.article-list article',
            'section.news-list article',
            'div.article-list article',
            'div.news-list article',
        ]
        
        # Try each selector until we find some containers
        for selector in container_selectors:
            containers = soup.select(selector)
            if containers:
                article_containers.extend(containers)
                if len(article_containers) >= 10:  # Don't need too many containers
                    article_containers = article_containers[:10]
                    break
        
        # If still no containers, try to find any article-like elements
        if not article_containers:
            article_containers = soup.find_all(['article', 'div'], class_=re.compile(r'(story|article|news|post|entry|item)', re.I))
        
        for container in article_containers[:15]:  # Slightly more in case some fail
            try:
                # Try multiple selectors for headline and URL
                headline_elem = None
                headline_selectors = [
                    'h3 a', 'h2 a', 'h4 a', 'h1 a',  # Headings with links
                    'a.headline', 'a.title', 'a.story-link',  # Common link classes
                    'a[itemprop="url"]',  # Schema.org markup
                    'h3', 'h2', 'h4',  # Just headings
                    'a'  # Fallback to any link
                ]
                
                # Try each selector until we find a good one
                for selector in headline_selectors:
                    elem = container.select_one(selector)
                    if elem and self.clean_text(elem.get_text()):
                        headline_elem = elem
                        break
                
                if not headline_elem:
                    continue
                
                # Get headline text
                headline = self.clean_text(headline_elem.get_text())
                if not headline or len(headline) < 15:  # Slightly shorter minimum length
                    continue
                
                # Get URL (either from the element or its parent)
                article_url = ''
                if headline_elem.name == 'a':
                    article_url = headline_elem.get('href', '')
                else:
                    # If it's a heading, try to find a link near it
                    link = headline_elem.find_parent('a') or headline_elem.find_next_sibling('a')
                    if link and link.get('href'):
                        article_url = link['href']
                
                # Clean and validate URL
                if not article_url or article_url.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                    
                article_url = self.make_absolute_url(article_url)
                
                # Extract summary using multiple possible selectors
                summary = ""
                summary_selectors = [
                    'p.summary', 'div.summary', 'p.snippet', 'div.article-summary', 
                    'p.story-body', 'div.story-body p', 'p.article-summary',
                    'div.excerpt', 'p.excerpt', 'div.description', 'p.description',
                    'div.entry-summary', 'p.entry-summary', 'div.entry-content p',
                    'p.article-snippet', 'div.article-snippet', 'p.dek', 'div.dek',
                    'p.lead', 'div.lead', 'p.article-lead', 'div.article-lead',
                    'p.article-intro', 'div.article-intro', 'p.intro', 'div.intro'
                ]
                
                # Try each summary selector
                for selector in summary_selectors:
                    summary_elems = container.select(selector)
                    if summary_elems:
                        summary = ' '.join([self.clean_text(p.get_text()) for p in summary_elems])
                        if len(summary) > 20:  # Only use if we have enough text
                            break
                
                # If no summary found, try to get first few paragraphs
                if not summary:
                    paragraphs = container.find_all('p')
                    if paragraphs:
                        summary = ' '.join([self.clean_text(p.get_text()) for p in paragraphs[:2]])
                
                # Extract image URL with multiple fallbacks
                image_url = ""
                img_selectors = [
                    'img[src]', 'img[data-src]', 'img[data-lazy-src]',
                    'div.image img', 'figure img', 'picture source',
                    'div.thumbnail img', 'div.media img', 'div.image-container img'
                ]
                
                for selector in img_selectors:
                    img_elem = container.select_one(selector)
                    if img_elem:
                        image_url = img_elem.get('data-src') or img_elem.get('src') or img_elem.get('data-lazy-src', '')
                        if image_url:
                            # Clean up image URL
                            image_url = image_url.split('?')[0].split('#')[0]
                            image_url = self.make_absolute_url(image_url)
                            break
                
                # Add the article to our list (without full text for now)
                article_data = {
                    'headline': headline[:200],  # Limit headline length
                    'url': article_url,
                    'summary': summary[:500],    # Limit summary length
                    'image': image_url,
                    'full_text': None  # We're not fetching full text for now
                }
                
                articles.append(article_data)
                
                # Be nice to the server (shorter delay since we're not fetching full content)
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
                
        return articles
        
    def fetch_full_article(self, url):
        """Stub method - we're not fetching full articles right now"""
        return None