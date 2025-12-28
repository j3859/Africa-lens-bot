from scrapers.base_scraper import BaseScraper
from utils.http_helper import fetch_page
from utils.logger import log_info, log_warning

class GenericScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []
        seen_urls = set()

        for a in soup.select("a[href]"):
            text = a.get_text().strip()
            href = a.get("href", "")
            
            if len(text) < 25 or len(text) > 200:
                continue
            if href in seen_urls:
                continue
            if any(x in text.lower() for x in [
                "cookie", "privacy", "subscribe", "contact", "menu", 
                "lire la suite", "read more", "en savoir plus", "aller au contenu",
                "newsletter", "login", "sign in", "recherche", "abonnez",
                "recevez", "suivez", "partager"
            ]):
                continue
            
            seen_urls.add(href)
            url = self.make_absolute_url(href)
            
            # Look for image in parent containers
            image = ""
            el = a
            for _ in range(5):
                el = el.find_parent()
                if not el:
                    break
                img = el.select_one("img")
                if img:
                    src = img.get("data-lazy-src") or img.get("data-src") or img.get("src") or ""
                    if src and not src.startswith("data:") and "logo" not in src.lower() and "icon" not in src.lower():
                        image = self.make_absolute_url(src)
                        break
            
            # Look for summary in same parent container
            summary = ""
            el = a
            for _ in range(3):
                el = el.find_parent()
                if not el:
                    break
                for selector in ["p", ".excerpt", ".summary", ".description", ".desc", ".chapo"]:
                    p = el.select_one(selector)
                    if p and p != a and len(p.get_text().strip()) > 30:
                        summary = self.clean_text(p.get_text())[:500]
                        break
                if summary:
                    break
            
            headline = self.clean_text(text)
            
            if headline and len(headline) > 15:
                articles.append({
                    "headline": headline,
                    "summary": summary,
                    "url": url,
                    "image": image
                })
            
            if len(articles) >= 15:
                break

        return articles
    
    def fetch_article_content(self, url):
        """Fetch full article content for AI generation"""
        try:
            html = fetch_page(url)
            if not html:
                return ""
            
            soup = self.get_soup(html)
            
            # 1. Try meta description first (most reliable)
            for meta_sel in ['meta[property="og:description"]', 'meta[name="description"]']:
                meta = soup.select_one(meta_sel)
                if meta:
                    desc = meta.get("content", "").strip()
                    if len(desc) > 50:
                        return desc[:1000]
            
            # Remove unwanted elements
            for tag in soup.select("script, style, nav, header, footer, aside, .ads, .advertisement, .social-share, .comments, .related"):
                tag.decompose()
            
            # 2. Try common article content selectors
            content_selectors = [
                ".field-name-body p",
                ".field--name-body p",
                ".article-content p",
                "article .content p", 
                ".post-content p", 
                ".entry-content p",
                ".story-body p",
                ".article-body p",
                "article p",
                "main p"
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    paragraphs = []
                    for el in elements[:5]:
                        text = el.get_text().strip()
                        # Skip short or boilerplate paragraphs
                        if len(text) > 40 and not any(x in text.lower() for x in ["cookie", "subscribe", "copyright", "fm:", "publi"]):
                            paragraphs.append(text)
                    if paragraphs:
                        content = " ".join(paragraphs)
                        if len(content) > 100:
                            return content[:1500]
            
            # 3. Fallback: get first substantial paragraphs
            paragraphs = soup.select("p")
            good_paragraphs = []
            for p in paragraphs:
                text = p.get_text().strip()
                if 50 < len(text) < 1000:
                    if not any(x in text.lower() for x in ["cookie", "subscribe", "copyright", "fm:", "publi"]):
                        good_paragraphs.append(text)
                if len(good_paragraphs) >= 3:
                    break
            
            if good_paragraphs:
                return " ".join(good_paragraphs)[:1500]
            
            return ""
            
        except Exception as e:
            return ""
    
    def enrich_article(self, article):
        """Fetch article page to get summary if missing"""
        if article.get("summary") and len(article["summary"]) > 50:
            return article
        
        content = self.fetch_article_content(article["url"])
        if content:
            article["summary"] = content[:500]
        
        return article