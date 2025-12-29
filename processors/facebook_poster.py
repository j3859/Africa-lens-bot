import os
import re
import requests
from utils.logger import log_info, log_error, log_success, log_warning

class FacebookPoster:
    def __init__(self):
        self.access_token = os.getenv("FB_ACCESS_TOKEN", "")
        self.page_id = os.getenv("FB_PAGE_ID", "")
        self.base_url = f"https://graph.facebook.com/v18.0/{self.page_id}"
    
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
            # Use a slightly longer timeout for validation
            response = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                # Some servers reject HEAD, try GET with stream
                response = requests.get(url, headers=headers, stream=True, timeout=15)
                if response.status_code != 200:
                    return False
                response.close()
            
            content_type = response.headers.get('content-type', '')
            if not any(t in content_type.lower() for t in ['image', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
                log_warning(f"Invalid content type: {content_type}")
                return False
            
            # Check file size (Facebook limit is 10MB approx)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 9 * 1024 * 1024:
                log_warning("Image too large")
                return False
            
            return True
            
        except Exception as e:
            log_warning(f"Image validation failed: {e}")
            return False
    
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
    
    def post(self, message, image_url="", country="africa", niche="news"):
        """Main post method - STRICT MODE (No fallbacks)"""
        
        if not self.access_token or not self.page_id:
            log_error("Facebook credentials not configured")
            return None
        
        if not image_url:
            log_error("Strict Mode: No image URL provided. Skipping post.")
            return None

        # Clean and validate image URL
        cleaned_url = self.clean_image_url(image_url)
        
        if self.validate_image_url(cleaned_url):
            log_info(f"Posting with image: {cleaned_url[:70]}...")
            result = self.post_with_image_url(message, cleaned_url)
            if result:
                log_success(f"Posted successfully. Post ID: {result}")
                return result
            else:
                log_error("Facebook API rejected the image post.")
        else:
            log_error("Image URL validation failed. Skipping post.")
        
        return None

fb_poster = FacebookPoster()