import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib
from utils.logger import log_info, log_warning, log_error

# Load .env file if it exists (for local development)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

class Database:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise Exception("SUPABASE_URL and SUPABASE_KEY must be set")
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def get_active_sources(self):
        """Get all active sources"""
        result = self.client.table("sources").select("*").eq("is_active", True).execute()
        return result.data if result.data else []
    
    def get_pending_content(self, country_code=None, language=None, niche=None, limit=10):
        """Get pending content with optional filters"""
        # Only select items strictly marked as 'pending'
        query = self.client.table("content").select("*").eq("status", "pending")
        
        if country_code and country_code != "Pan":
            query = query.eq("country_code", country_code)
        
        if language:
            query = query.eq("source_language", language)
        
        if niche:
            query = query.eq("niche", niche)
        
        query = query.limit(limit)
        result = query.execute()
        
        return result.data if result.data else []
    
    def get_current_schedule(self):
        """Get schedule for current hour"""
        current_hour = datetime.utcnow().hour
        result = self.client.table("schedule").select("*").eq("hour_utc", current_hour).eq("is_active", True).execute()
        return result.data[0] if result.data else None
    
    def get_full_schedule(self):
        """Get full 24-hour schedule"""
        result = self.client.table("schedule").select("*").order("hour_utc").execute()
        return result.data if result.data else []
    
    def add_content(self, source_id, headline, summary, original_url, image_url, source_language, country, country_code, niche):
        """Add new content to database"""
        
        # --- STRICT CHECK: REJECT CONTENT WITHOUT IMAGES ---
        if not image_url or str(image_url).strip() == "":
            log_warning(f"Rejected article - No image URL provided for: {headline[:50]}...")
            return False
        # ---------------------------------------------------

        headline_hash = self.create_headline_hash(headline)
        
        if self.content_exists(headline_hash):
            log_warning(f"Rejected article - Duplicate headline: {headline[:50]}...")
            return False
        
        if self.url_exists(original_url):
            log_warning(f"Rejected article - Duplicate URL: {original_url}")
            return False
        
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
            "status": "pending",
            "headline_hash": headline_hash,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = self.client.table("content").insert(data).execute()
            log_info(f"Successfully inserted article into database: {headline[:50]}...")
            return True
        except Exception as e:
            log_error(f"Database error while inserting article: {e}")
            return False
    
    def content_exists(self, headline_hash):
        """Check if content already exists"""
        result = self.client.table("content").select("id").eq("headline_hash", headline_hash).execute()
        return len(result.data) > 0 if result.data else False
    
    def url_exists(self, url):
        """Check if content with same URL already exists"""
        if not url:
            return False
        result = self.client.table("content").select("id").eq("original_url", url).execute()
        return len(result.data) > 0 if result.data else False
    
    def create_headline_hash(self, headline):
        """Create hash of headline for duplicate detection"""
        normalized = " ".join(headline.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def mark_content_posted(self, content_id):
        """Mark content as posted"""
        self.client.table("content").update({
            "status": "posted"
        }).eq("id", content_id).execute()
    
    def mark_content_failed(self, content_id):
        """Mark content as failed"""
        self.client.table("content").update({"status": "failed"}).eq("id", content_id).execute()

    def mark_content_skipped_image(self, content_id):
        """Mark content as skipped due to invalid/missing image"""
        self.client.table("content").update({"status": "skipped_no_image"}).eq("id", content_id).execute()
    
    def is_content_posted(self, content_id):
        """Check if content has already been posted"""
        result = self.client.table("content").select("status").eq("id", content_id).execute()
        if result.data:
            return result.data[0].get("status") == "posted"
        return False
    
    def is_image_used(self, image_url):
        """Check if this specific image URL has been used in a previous post"""
        if not image_url:
            return True 
            
        result = self.client.table("posts").select("id").eq("image_used", image_url).execute()
        return len(result.data) > 0 if result.data else False
    
    def create_post(self, content_id, post_text, post_language, target_country, niche, image_used, facebook_post_id):
        """Create a post record"""
        if self.is_content_posted(content_id):
            return False
        
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
        
        self.client.table("posts").insert(data).execute()
        return True
    
    def get_recent_posts(self, limit=10):
        """Get recent posts"""
        result = self.client.table("posts").select("*").order("posted_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    def get_language_ratio(self, hours=24):
        """Get current language ratio for specified hours"""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        result = self.client.table("posts").select("post_language").gte("posted_at", cutoff).execute()
        posts = result.data if result.data else []
        
        french = sum(1 for p in posts if p.get("post_language") == "french")
        english = sum(1 for p in posts if p.get("post_language") == "english")
        total = french + english
        
        french_ratio = french / total if total > 0 else 0.7
        english_ratio = english / total if total > 0 else 0.3
        
        return {
            "french": french,
            "english": english,
            "total": total,
            "french_ratio": french_ratio,
            "english_ratio": english_ratio,
            "french_pct": french_ratio * 100,
            "english_pct": english_ratio * 100
        }
    
    def update_source_scraped(self, source_id):
        """Update last scraped timestamp for source"""
        self.client.table("sources").update({
            "last_scraped": datetime.utcnow().isoformat()
        }).eq("id", source_id).execute()
    
    def get_sources_needing_scrape(self, hours=4):
        """Get sources that need scraping"""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        result = self.client.table("sources").select("*").eq("is_active", True).or_(
            f"last_scraped.is.null,last_scraped.lt.{cutoff}"
        ).execute()
        
        return result.data if result.data else []

    def cleanup_old_content(self, hours=48):
        """Delete content older than X hours that hasn't been posted"""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        # We delete anything OLDER than cutoff that is NOT 'posted'
        # This keeps our history for image uniqueness, but cleans up the junk (failed, skipped, pending-forever)
        try:
            result = self.client.table("content").delete()\
                .lt("created_at", cutoff)\
                .neq("status", "posted")\
                .execute()
            
            # Return count of deleted items
            count = len(result.data) if result.data else 0
            return count
        except Exception as e:
            print(f"Cleanup error: {e}")
            return 0