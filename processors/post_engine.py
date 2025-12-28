from utils.database import Database
from processors.ai_processor import ai_processor
from processors.facebook_poster import fb_poster
from processors.content_selector import content_selector
from utils.logger import log_info, log_error, log_success

class PostEngine:
    def __init__(self):
        self.db = Database()
        self.ai = ai_processor
        self.fb = fb_poster
        self.selector = content_selector

    def run_single_post(self, schedule=None):
        """Run a single post cycle"""
        try:
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
            
            # Select content based on schedule
            result = self.selector.select_content(schedule)
            
            if not result:
                log_info("No suitable content found")
                return False
            
            # Handle if result is tuple (content, language) or just content dict
            if isinstance(result, tuple):
                content, suggested_language = result
            else:
                content = result
                suggested_language = None
            
            if not content:
                log_info("No suitable content found")
                return False
            
            log_info(f"Selected: [{content.get('country', 'Unknown')}] {content.get('headline', '')[:50]}...")
            
            # Determine output language
            output_language = suggested_language or schedule.get('target_language') or content.get('source_language', 'french')
            log_info(f"Output language: {output_language}")
            
            # Generate post with AI
            post_text = self.ai.generate_post(
                headline=content.get('headline', ''),
                summary=content.get('summary', ''),
                output_language=output_language,
                country=content.get('country', ''),
                niche=content.get('niche', '')
            )
            
            if not post_text:
                log_error("Failed to generate post text")
                return False
            
            # Get image URL
            image_url = content.get('image_url', '')
            
            # Post to Facebook
            post_result = self.fb.post(post_text, image_url)
            
            if post_result:
                # Mark content as posted
                self.db.mark_content_posted(content['id'])
                
                # Save to posts table
                self.db.create_post(
                    content_id=content['id'],
                    post_text=post_text,
                    post_language=output_language,
                    target_country=content.get('country', ''),
                    niche=content.get('niche', ''),
                    image_used=image_url,
                    facebook_post_id=post_result
                )
                
                log_success(f"Post cycle completed successfully")
                
                return True
            else:
                log_error("Failed to post to Facebook")
                return False
                
        except Exception as e:
            log_error(f"Post cycle error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_scheduled_post(self):
        """Run post based on current schedule"""
        return self.run_single_post()

post_engine = PostEngine()