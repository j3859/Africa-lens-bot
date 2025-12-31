import sys
import os
import schedule
import time
from datetime import datetime
from processors.post_engine import post_engine
from processors.scraper_runner import scraper_runner
from processors.telegram_reporter import telegram_reporter
from utils.database import Database
from utils.fb_analytics import fb_analytics
from utils.logger import log_info, log_error, log_success

class AfricaLensBot:
    def __init__(self):
        self.db = Database()
        self.post_engine = post_engine
        self.scraper = scraper_runner
        self.reporter = telegram_reporter
        self.analytics = fb_analytics
    
    def show_status(self):
        """Show current bot status"""
        try:
            pending_result = self.db.client.table("content").select("id").eq("status", "pending").execute()
            pending = len(pending_result.data) if pending_result.data else 0
            
            today = datetime.utcnow().date().isoformat()
            posts_result = self.db.client.table("posts").select("id").gte("posted_at", today).execute()
            posted_today = len(posts_result.data) if posts_result.data else 0
            
            french_result = self.db.client.table("posts").select("id").gte("posted_at", today).eq("post_language", "french").execute()
            english_result = self.db.client.table("posts").select("id").gte("posted_at", today).eq("post_language", "english").execute()
            french_count = len(french_result.data) if french_result.data else 0
            english_count = len(english_result.data) if english_result.data else 0
            
            print("="*50)
            print("AFRICA LENS BOT STATUS")
            print("="*50)
            print(f"Pending content: {pending}")
            print(f"Posts today: {posted_today}")
            print(f"  - French: {french_count}")
            print(f"  - English: {english_count}")
            print(f"Current time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
            print("="*50)
            
        except Exception as e:
            print(f"Error getting status: {e}")
    
    def run_once(self):
        """Run a single post"""
        log_info("Running single post cycle...")
        self.post_engine.run_scheduled_post()
    
    def run_scrape(self):
        """Run all scrapers"""
        log_info("Running scrapers...")
        self.scraper.run_all()
    
    def run_cleanup(self, hours=48):
        """Clean up old content"""
        log_info(f"Cleaning up content older than {hours} hours...")
        try:
            count = self.db.cleanup_old_content(hours=hours)
            log_success(f"Cleanup complete. Removed {count} old records.")
            return count
        except Exception as e:
            log_error(f"Error during cleanup: {e}")
            return 0
    
    def update_analytics(self):
        """Update analytics for recent posts"""
        log_info("Updating analytics...")
        self.analytics.update_all_recent_posts(hours=24)
    
    def show_analytics(self):
        """Show analytics report"""
        self.analytics.print_report(days=7)
    
    def run_continuous(self):
        """Run continuously with schedule"""
        log_info("Starting Africa Lens Bot in continuous mode...")
        
        # Send startup notification
        self.reporter.send_startup_message()
        
        # Schedule hourly posts at :05
        schedule.every().hour.at(":05").do(self.run_once)
        
        # Schedule scraping every 3 hours
        schedule.every(3).hours.do(self.run_scrape)
        
        # Schedule cleanup daily at 3 AM UTC
        schedule.every().day.at("03:00").do(lambda: self.run_cleanup(hours=48))
        
        # Schedule analytics update every 6 hours
        schedule.every(6).hours.do(self.update_analytics)
        
        # Schedule daily report at midnight UTC
        schedule.every().day.at("00:00").do(self.reporter.send_daily_report)
        
        # Schedule weekly report on Sundays
        schedule.every().sunday.at("12:00").do(self.reporter.send_weekly_report)
        
        # Run initial tasks
        self.run_scrape()
        self.run_cleanup()  # Run cleanup on startup
        
        log_info("Bot running. Press Ctrl+C to stop.")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                log_info("Bot stopped by user")
                break
            except Exception as e:
                log_error(f"Error in main loop: {e}")
                self.reporter.send_error_alert(str(e))
                time.sleep(300)

if __name__ == "__main__":
    bot = AfricaLensBot()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py [status|post|scrape|run|report|analytics|cleanup]")
        print("\nCommands:")
        print("  status    - Show current bot status")
        print("  post      - Run a single post cycle")
        print("  scrape    - Run all scrapers")
        print("  cleanup   - Clean up old content (48h by default)")
        print("  run       - Run in continuous mode")
        print("  report    - Send daily report")
        print("  analytics - Show analytics report")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        bot.show_status()
    elif command == "post":
        bot.run_once()
    elif command == "scrape":
        bot.run_scrape()
    elif command == "cleanup":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 48
        bot.run_cleanup(hours=hours)
    elif command == "run":
        bot.run_continuous()
    elif command == "report":
        bot.reporter.send_daily_report()
        print("Report sent (if Telegram configured)")
    elif command == "analytics":
        bot.show_analytics()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, post, scrape, cleanup, run, report, analytics")