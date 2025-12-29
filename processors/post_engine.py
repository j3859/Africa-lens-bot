from utils.database import Database
from processors.ai_processor import ai_processor
from processors.facebook_poster import fb_poster
from processors.content_selector import content_selector
from utils.logger import log_info, log_error, log_success, log_warning
import time

class PostEngine:
    def __init__(self):
        self.db = Database()
        self.ai = ai_processor
        self.fb = fb_poster
        self.selector = content_selector
        self.MAX_RETRIES = 5  # How many articles to check for valid images before giving up

    def run_single_post(self, schedule=None):
        """Run a single post cycle with retries for valid images"""
        
        # Get schedule for current hour if not provided
        if not schedule:
            schedule = self.db.get_current_schedule()
        
        if not schedule:
            log_info("No schedule for current hour, using defaults")
            schedule = {
                "target_country": "Pan-African",
                "target_language": "french",
                "target_niche": "politics"
            }
        
        log_info(f"Schedule: {schedule.get('target_country', 'Any')} | {schedule.get('target_language', 'any')} | {schedule.get('target_niche', 'any')}")

        attempts = 0
        while attempts < self.MAX_RETRIES:
            attempts += 1
            log_info(f"Attempt {attempts}/{self.MAX_RETRIES} to find content with valid image...")

            # Select content based on schedule
            # Note: The selector fetches 'pending' content. Since we mark bad content 
            # as 'skipped_no_image' inside this loop, the next iteration will fetch different content.
            result = self.selector.select_content(schedule)
            
            if not result or (isinstance(result, tuple) and not result[0]):
                log_info("No suitable content found in DB.")
                return False
            
            # Handle if result is tuple (content, language) or just content dict
            if isinstance(result, tuple):
                content, suggested_language = result
            else:
                content = result
                suggested_language = None
            
            # 1. Check if content has an image URL at all
            raw_image_url = content.get('image_url', '')
            if not raw_image_url:
                log_warning(f"Content {content['id']} has no image URL. Skipping.")
                self.db.mark_content_skipped_image(content['id'])
                continue

            # 2. Check if image has been used before (Strict Uniqueness)
            cleaned_url = self.fb.clean_image_url(raw_image_url)
            if self.db.is_image_used(cleaned_url):
                log_warning(f"Image {cleaned_url[:50]}... already used in previous post. Skipping.")
                self.db.mark_content_skipped_image(content['id'])
                continue

            # 3. Validate image accessibility/quality
            if not self.fb.validate_image_url(cleaned_url):
                log_warning(f"Image validation failed for {cleaned_url[:50]}... Skipping.")
                self.db.mark_content_skipped_image(content['id'])
                continue

            # --- If we get here, the image is VALID and UNIQUE ---
            
            country = content.get('country', 'Pan-African')
            niche = content.get('niche', 'politics')
            
            log_info(f"Selected Valid Content: [{country}] {content.get('headline', '')[:50]}...")
            
            # Determine output language
            output_language = suggested_language or schedule.get('target_language') or content.get('source_language', 'french')
            
            # Generate post with AI
            post_text = self.ai.generate_post(
                headline=content.get('headline', ''),
                summary=content.get('summary', ''),
                output_language=output_language,
                country=country,
                niche=niche
            )
            
            if not post_text:
                log_error("Failed to generate post text")
                self.db.mark_content_failed(content['id'])
                continue # Try next article
            
            # Mark content as posted BEFORE posting to prevent duplicates
            self.db.mark_content_posted(content['id'])
            
            # Post to Facebook (Strict mode: will fail if image fails upload)
            post_result = self.fb.post(post_text, cleaned_url, country=country, niche=niche)
            
            if post_result:
                # Save to posts table
                self.db.create_post(
                    content_id=content['id'],
                    post_text=post_text,
                    post_language=output_language,
                    target_country=country,
                    niche=niche,
                    image_used=cleaned_url,
                    facebook_post_id=post_result
                )
                log_success(f"Post cycle completed successfully")
                return True
            else:
                # If posting failed (API error), mark content as failed
                log_error("Facebook Post failed after validation. Marking failed.")
                self.db.mark_content_failed(content['id'])
                # We do not continue the loop here; if the API is broken, we should probably stop.
                return False
                
        log_warning("Max retries reached. Could not find valid content with images.")
        return False
    
    def run_scheduled_post(self):
        """Run post based on current schedule"""
        return self.run_single_post()

post_engine = PostEngine()