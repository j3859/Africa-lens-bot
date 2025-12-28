import requests
from config.settings import FB_ACCESS_TOKEN, FB_PAGE_ID, FB_BASE_URL
from utils.logger import log_info, log_error, log_success
from utils.http_helper import download_image
import tempfile
import os

class FacebookPoster:
    def __init__(self):
        self.access_token = FB_ACCESS_TOKEN
        self.page_id = FB_PAGE_ID
        self.base_url = FB_BASE_URL
    
    def post_text_only(self, message):
        url = f"{self.base_url}/{self.page_id}/feed"
        
        payload = {
            "message": message,
            "access_token": self.access_token
        }
        
        try:
            response = requests.post(url, data=payload)
            result = response.json()
            
            if "id" in result:
                log_success(f"Posted successfully. Post ID: {result['id']}")
                return result["id"]
            else:
                log_error(f"Facebook API error: {result}")
                return None
        
        except Exception as e:
            log_error(f"Failed to post: {e}")
            return None
    
    def post_with_image_url(self, message, image_url):
        # STRATEGY 1: Download and upload (bypasses hotlink protection)
        image_data = download_image(image_url)
        if image_data:
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                    temp.write(image_data)
                    temp_path = temp.name
                
                url = f"{self.base_url}/{self.page_id}/photos"
                payload = {
                    "message": message,
                    "access_token": self.access_token
                }
                files = {
                    "source": open(temp_path, "rb")
                }
                
                log_info(f"Uploading image from {temp_path}...")
                response = requests.post(url, data=payload, files=files)
                result = response.json()
                
                # Cleanup
                files["source"].close()
                os.unlink(temp_path)
                
                if "id" in result or "post_id" in result:
                    post_id = result.get("post_id", result.get("id"))
                    log_success(f"Posted text+image (uploaded). Post ID: {post_id}")
                    return post_id
                else:
                    log_error(f"FB Upload Error: {result}")
                    # Continue to Strategy 2
            except Exception as e:
                log_error(f"Image upload failed: {e}")
                # Continue to Strategy 2
        
        # STRATEGY 2: Send URL (Facebook fetches it)
        log_info(f"Attempting to post with image URL directly: {image_url}")
        url = f"{self.base_url}/{self.page_id}/photos"
        
        payload = {
            "message": message,
            "url": image_url,
            "access_token": self.access_token
        }
        
        try:
            response = requests.post(url, data=payload)
            result = response.json()
            
            if "id" in result or "post_id" in result:
                post_id = result.get("post_id", result.get("id"))
                log_success(f"Posted with image URL. Post ID: {post_id}")
                return post_id
            else:
                log_error(f"FB URL Post Error: {result}")
                log_info("Falling back to text-only post")
                return self.post_text_only(message)
        
        except Exception as e:
            log_error(f"Failed to post with image: {e}")
            return self.post_text_only(message)
    
    def post(self, message, image_url=None):
        if image_url and image_url.startswith("http"):
            return self.post_with_image_url(message, image_url)
        else:
            return self.post_text_only(message)
    
    def verify_token(self):
        url = f"{self.base_url}/me"
        params = {"access_token": self.access_token}
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            
            if "id" in result:
                log_success(f"Token valid. Page: {result.get('name', 'Unknown')}")
                return True
            else:
                log_error(f"Token invalid: {result}")
                return False
        
        except Exception as e:
            log_error(f"Token verification failed: {e}")
            return False

fb_poster = FacebookPoster()