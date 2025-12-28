import os
import re
import requests
from utils.logger import log_info, log_error, log_success, log_warning

class FacebookPoster:
    def __init__(self):
        self.access_token = os.getenv("FB_ACCESS_TOKEN", "")
        self.page_id = os.getenv("FB_PAGE_ID", "")
        self.base_url = f"https://graph.facebook.com/v18.0/{self.page_id}"
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
    
    def clean_image_url(self, url):
        """Extract real image URL from CDN/proxy URLs"""
        if not url:
            return ""
        
        # Pattern 1: cdn4.premiumread.com/?url=REAL_URL&...
        if "premiumread.com" in url:
            match = re.search(r'url=([^&]+)', url)
            if match:
                url = requests.utils.unquote(match.group(1))
        
        # Pattern 2: images.weserv.nl/?url=REAL_URL
        if "weserv.nl" in url:
            match = re.search(r'url=([^&]+)', url)
            if match:
                url = requests.utils.unquote(match.group(1))
        
        # Pattern 3: wp.com proxy
        if "wp.com" in url and "i0.wp.com" in url or "i1.wp.com" in url or "i2.wp.com" in url:
            url = re.sub(r'https?://i\d\.wp\.com/', 'https://', url)
        
        # Ensure URL has protocol
        if url and not url.startswith("http"):
            url = "https://" + url
        
        return url
    
    def validate_image_url(self, url):
        """Check if image URL is accessible and valid"""
        if not url:
            return False
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                return False
            
            content_type = response.headers.get('content-type', '')
            if not any(t in content_type.lower() for t in ['image', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
                return False
            
            # Check file size (Facebook limit is 10MB)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:
                return False
            
            return True
            
        except Exception as e:
            log_warning(f"Image validation failed: {e}")
            return False
    
    def get_fallback_image(self, query="africa news"):
        """Get fallback image from Unsplash or Pexels"""
        
        # Try Unsplash first
        if self.unsplash_key:
            try:
                url = f"https://api.unsplash.com/photos/random?query={query}&orientation=landscape"
                headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    image_url = data.get("urls", {}).get("regular", "")
                    if image_url:
                        log_info("Using Unsplash fallback image")
                        return image_url
            except Exception as e:
                log_warning(f"Unsplash fallback failed: {e}")
        
        # Try Pexels
        if self.pexels_key:
            try:
                url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape"
                headers = {"Authorization": self.pexels_key}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    photos = data.get("photos", [])
                    if photos:
                        image_url = photos[0].get("src", {}).get("large", "")
                        if image_url:
                            log_info("Using Pexels fallback image")
                            return image_url
            except Exception as e:
                log_warning(f"Pexels fallback failed: {e}")
        
        return ""
    
    def post_with_image_url(self, message, image_url):
        """Post with image URL directly"""
        try:
            url = f"{self.base_url}/photos"
            data = {
                "url": image_url,
                "caption": message,
                "access_token": self.access_token
            }
            
            response = requests.post(url, data=data, timeout=60)
            result = response.json()
            
            if "id" in result:
                return result["id"]
            elif "error" in result:
                log_error(f"FB Photo Post Error: {result['error'].get('message', 'Unknown error')}")
                return None
            
            return None
            
        except Exception as e:
            log_error(f"FB post with image URL error: {e}")
            return None
    
    def post_text_only(self, message):
        """Post text only without image"""
        try:
            url = f"{self.base_url}/feed"
            data = {
                "message": message,
                "access_token": self.access_token
            }
            
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            
            if "id" in result:
                return result["id"]
            elif "error" in result:
                log_error(f"FB Text Post Error: {result['error'].get('message', 'Unknown error')}")
                return None
            
            return None
            
        except Exception as e:
            log_error(f"FB text post error: {e}")
            return None
    
    def post(self, message, image_url="", country="africa", niche="news"):
        """Main post method with fallback logic"""
        
        if not self.access_token or not self.page_id:
            log_error("Facebook credentials not configured")
            return None
        
        # Step 1: Clean and validate image URL
        if image_url:
            cleaned_url = self.clean_image_url(image_url)
            log_info(f"Cleaned image URL: {cleaned_url[:70]}...")
            
            if self.validate_image_url(cleaned_url):
                log_info("Image URL validated, posting with image...")
                result = self.post_with_image_url(message, cleaned_url)
                if result:
                    log_success(f"Posted with image. Post ID: {result}")
                    return result
                else:
                    log_warning("Image post failed, trying fallback...")
            else:
                log_warning("Image URL validation failed")
        
        # Step 2: Try fallback image from Unsplash/Pexels
        fallback_query = f"{country} {niche}".replace("Pan-African", "africa")
        fallback_url = self.get_fallback_image(fallback_query)
        
        if fallback_url:
            log_info("Attempting post with fallback image...")
            result = self.post_with_image_url(message, fallback_url)
            if result:
                log_success(f"Posted with fallback image. Post ID: {result}")
                return result
        
        # Step 3: Fall back to text-only post
        log_info("Posting text-only...")
        result = self.post_text_only(message)
        
        if result:
            log_success(f"Posted text-only. Post ID: {result}")
            return result
        
        log_error("All posting attempts failed")
        return None


fb_poster = FacebookPoster()