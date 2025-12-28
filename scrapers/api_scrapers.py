import os
import requests
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from utils.logger import log_info, log_warning

class GNewsAPIScraper(BaseScraper):
    """Scraper for GNews API - African news in French and English"""
    
    def __init__(self, source_id, name, url, country, country_code, language, niche):
        super().__init__(source_id, name, url, country, country_code, language, niche)
        self.api_key = os.getenv("GNEWS_KEY", "")
        self.base_url = "https://gnews.io/api/v4"
    
    def parse_articles(self, html=None):
        """Fetch articles from GNews API"""
        if not self.api_key:
            return []
        
        articles = []
        
        queries = [
            {"q": "afrique", "lang": "fr"},
            {"q": "africa", "lang": "en"},
            {"q": "senegal OR mali OR burkina", "lang": "fr"},
            {"q": "nigeria OR kenya OR ghana", "lang": "en"},
        ]
        
        seen_urls = set()
        
        for query_params in queries:
            try:
                url = f"{self.base_url}/search?q={query_params['q']}&lang={query_params['lang']}&max=10&token={self.api_key}"
                response = requests.get(url, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                for item in data.get("articles", []):
                    article_url = item.get("url", "")
                    
                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)
                    
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    content_text = (title + " " + desc).lower()
                    
                    country = "Pan-African"
                    country_code = "Pan"
                    
                    country_keywords = {
                        "nigeria": ("Nigeria", "NG"),
                        "kenya": ("Kenya", "KE"),
                        "senegal": ("Senegal", "SN"),
                        "mali": ("Mali", "ML"),
                        "burkina": ("Burkina Faso", "BF"),
                        "congo": ("DRC", "CD"),
                        "burundi": ("Burundi", "BI"),
                        "ghana": ("Ghana", "GH"),
                        "south africa": ("South Africa", "ZA"),
                        "morocco": ("Morocco", "MA"),
                    }
                    
                    for keyword, (country_name, code) in country_keywords.items():
                        if keyword in content_text:
                            country = country_name
                            country_code = code
                            break
                    
                    articles.append({
                        "headline": title,
                        "summary": desc or "",
                        "url": article_url,
                        "image": item.get("image", ""),
                        "country": country,
                        "country_code": country_code,
                        "language": query_params["lang"],
                        "published_at": item.get("publishedAt", ""),
                    })
                    
                    if len(articles) >= 15:
                        break
                        
            except Exception as e:
                continue
            
            if len(articles) >= 15:
                break
        
        return articles[:15]


class YouTubeAPIScraper(BaseScraper):
    """Scraper for YouTube Data API - African news videos"""
    
    def __init__(self, source_id, name, url, country, country_code, language, niche):
        super().__init__(source_id, name, url, country, country_code, language, niche)
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def parse_articles(self, html=None):
        """Fetch videos from YouTube API"""
        if not self.api_key:
            return []
        
        articles = []
        
        queries = [
            ("actualites afrique", "fr"),
            ("africa news today", "en"),
            ("nigeria news", "en"),
        ]
        
        seen_ids = set()
        
        for query, lang in queries:
            try:
                url = f"{self.base_url}/search?part=snippet&q={query}&type=video&maxResults=5&order=date&key={self.api_key}"
                response = requests.get(url, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                for item in data.get("items", []):
                    video_id = item.get("id", {}).get("videoId", "")
                    
                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)
                    
                    snippet = item.get("snippet", {})
                    
                    articles.append({
                        "headline": snippet.get("title", ""),
                        "summary": snippet.get("description", "")[:500],
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "image": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "country": "Pan-African",
                        "country_code": "Pan",
                        "language": lang,
                        "published_at": snippet.get("publishedAt", ""),
                    })
                    
                    if len(articles) >= 10:
                        break
                        
            except Exception as e:
                continue
            
            if len(articles) >= 10:
                break
        
        return articles[:10]


class NewsAPIScraper(BaseScraper):
    """Scraper for NewsAPI - African news"""
    
    def __init__(self, source_id, name, url, country, country_code, language, niche):
        super().__init__(source_id, name, url, country, country_code, language, niche)
        self.api_key = os.getenv("NEWSAPI_KEY", "")
        self.base_url = "https://newsapi.org/v2"
    
    def parse_articles(self, html=None):
        """Fetch articles from NewsAPI"""
        if not self.api_key:
            return []
        
        articles = []
        seen_urls = set()
        
        queries = [
            ("africa", "en"),
            ("nigeria", "en"),
            ("kenya", "en"),
            ("south africa", "en"),
        ]
        
        for query, lang in queries:
            try:
                url = f"{self.base_url}/everything?q={query}&language={lang}&pageSize=5&sortBy=publishedAt&apiKey={self.api_key}"
                response = requests.get(url, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                for item in data.get("articles", []):
                    article_url = item.get("url", "")
                    
                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)
                    
                    title = item.get("title", "")
                    if not title or title == "[Removed]":
                        continue
                    
                    content_text = (title + " " + (item.get("description") or "")).lower()
                    
                    country = "Pan-African"
                    country_code = "Pan"
                    
                    country_keywords = {
                        "nigeria": ("Nigeria", "NG"),
                        "kenya": ("Kenya", "KE"),
                        "ghana": ("Ghana", "GH"),
                        "south africa": ("South Africa", "ZA"),
                        "egypt": ("Egypt", "EG"),
                    }
                    
                    for keyword, (country_name, code) in country_keywords.items():
                        if keyword in content_text:
                            country = country_name
                            country_code = code
                            break
                    
                    articles.append({
                        "headline": title,
                        "summary": item.get("description", "") or "",
                        "url": article_url,
                        "image": item.get("urlToImage", ""),
                        "country": country,
                        "country_code": country_code,
                        "language": lang,
                        "published_at": item.get("publishedAt", ""),
                    })
                    
                    if len(articles) >= 15:
                        break
                        
            except Exception as e:
                continue
            
            if len(articles) >= 15:
                break
        
        return articles[:15]


class GoogleTrendsScraper(BaseScraper):
    """Scraper for Google Trends - Trending in Africa"""
    
    def __init__(self, source_id, name, url, country, country_code, language, niche):
        super().__init__(source_id, name, url, country, country_code, language, niche)
    
    def parse_articles(self, html=None):
        """Fetch trending topics from Google Trends"""
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='en-US', tz=0)
            
            articles = []
            countries = [
                ("south_africa", "South Africa", "ZA"),
                ("nigeria", "Nigeria", "NG"),
                ("kenya", "Kenya", "KE"),
            ]
            
            for geo, country_name, code in countries:
                try:
                    trending = pytrends.trending_searches(pn=geo)
                    
                    for idx, topic in enumerate(trending[0].tolist()[:3]):
                        articles.append({
                            "headline": f"Trending: {topic}",
                            "summary": f"Currently trending in {country_name}",
                            "url": f"https://trends.google.com/trends/explore?geo={code}&q={topic}",
                            "image": "",
                            "country": country_name,
                            "country_code": code,
                            "language": "english",
                        })
                except Exception:
                    continue
            
            return articles[:10]
            
        except ImportError:
            return []
        except Exception as e:
            return []