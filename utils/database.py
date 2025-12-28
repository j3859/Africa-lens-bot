from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timedelta
import hashlib

class Database:
    def __init__(self):
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def get_active_sources(self, priority=None, country_code=None, niche=None):
        query = self.client.table("sources").select("*").eq("is_active", True)
        if priority:
            query = query.eq("priority", priority)
        if country_code:
            query = query.eq("country_code", country_code)
        if niche:
            query = query.eq("niche", niche)
        return query.execute().data
    
    def get_sources_needing_scrape(self):
        sources = self.get_active_sources()
        needs_scrape = []
        for source in sources:
            if source["last_scraped"] is None:
                needs_scrape.append(source)
            else:
                last = datetime.fromisoformat(source["last_scraped"].replace("Z", "+00:00"))
                hours = (datetime.now(last.tzinfo) - last).total_seconds() / 3600
                if hours >= source["scrape_frequency_hours"]:
                    needs_scrape.append(source)
        return needs_scrape
    
    def update_source_scraped(self, source_id):
        self.client.table("sources").update({"last_scraped": datetime.utcnow().isoformat()}).eq("id", source_id).execute()
    
    def create_headline_hash(self, headline):
        return hashlib.sha256(headline.lower().strip().encode()).hexdigest()
    
    def content_exists(self, headline):
        h = self.create_headline_hash(headline)
        result = self.client.table("content").select("id").eq("headline_hash", h).execute()
        return len(result.data) > 0
    
    def add_content(self, source_id, headline, summary, original_url, image_url, source_language, country, country_code, niche):
        if self.content_exists(headline):
            return None
        data = {
            "source_id": source_id,
            "headline": headline,
            "summary": summary,
            "original_url": original_url,
            "image_url": image_url,
            "source_language": source_language,
            "country": country,
            "country_code": country_code,
            "niche": niche,
            "headline_hash": self.create_headline_hash(headline),
            "status": "pending"
        }
        result = self.client.table("content").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_pending_content(self, language=None, country_code=None, niche=None, limit=10):
        query = self.client.table("content").select("*").eq("status", "pending")
        if language:
            query = query.eq("source_language", language)
        if country_code:
            query = query.eq("country_code", country_code)
        if niche:
            query = query.eq("niche", niche)
        return query.order("fetched_at", desc=True).limit(limit).execute().data
    
    def mark_content_posted(self, content_id):
        self.client.table("content").update({"status": "posted"}).eq("id", content_id).execute()
    
    def mark_content_failed(self, content_id):
        self.client.table("content").update({"status": "failed"}).eq("id", content_id).execute()
    
    def create_post(self, content_id, post_text, post_language, target_country, niche, image_used, facebook_post_id):
        data = {
            "content_id": content_id,
            "post_text": post_text,
            "post_language": post_language,
            "target_country": target_country,
            "niche": niche,
            "image_used": image_used,
            "facebook_post_id": facebook_post_id,
            "posted_at": datetime.utcnow().isoformat()
        }
        result = self.client.table("posts").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_recent_posts(self, hours=24):
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        return self.client.table("posts").select("*").gte("posted_at", since).execute().data
    
    def get_language_ratio(self, hours=24):
        posts = self.get_recent_posts(hours)
        if not posts:
            return {"french": 0, "english": 0, "total": 0, "french_pct": 0, "english_pct": 0}
        french = sum(1 for p in posts if p["post_language"] == "french")
        english = sum(1 for p in posts if p["post_language"] == "english")
        total = len(posts)
        return {"french": french, "english": english, "total": total, "french_pct": round(french/total*100,1) if total else 0, "english_pct": round(english/total*100,1) if total else 0}
    
    def get_current_schedule(self):
        hour = datetime.utcnow().hour
        result = self.client.table("schedule").select("*").eq("hour_utc", hour).eq("is_active", True).execute()
        return result.data[0] if result.data else None
    
    def get_full_schedule(self):
        return self.client.table("schedule").select("*").eq("is_active", True).order("hour_utc").execute().data

db = Database()