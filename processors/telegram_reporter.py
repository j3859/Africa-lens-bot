import os
import requests
from datetime import datetime, timedelta
from utils.database import Database
from utils.fb_analytics import fb_analytics
from utils.logger import log_info, log_error, log_success

class TelegramReporter:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.db = Database()
        self.analytics = fb_analytics
    
    def send_message(self, message):
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            log_info("Telegram not configured - skipping report")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                log_success("Telegram report sent")
                return True
            else:
                log_error(f"Telegram error: {response.status_code}")
                return False
                
        except Exception as e:
            log_error(f"Telegram send error: {e}")
            return False
    
    def generate_daily_report(self):
        """Generate daily performance report with analytics"""
        try:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            # Update metrics for recent posts first
            self.analytics.update_all_recent_posts(hours=48)
            
            # Get posts from last 24 hours
            posts_result = self.db.client.table("posts").select("*").gte(
                "posted_at", yesterday.isoformat()
            ).execute()
            
            posts = posts_result.data if posts_result.data else []
            
            # Count by language
            french_posts = sum(1 for p in posts if p.get('post_language') == 'french')
            english_posts = sum(1 for p in posts if p.get('post_language') == 'english')
            
            # Count by country
            countries = {}
            for p in posts:
                country = p.get('target_country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
            
            # Count by niche
            niches = {}
            for p in posts:
                niche = p.get('niche', 'Unknown')
                niches[niche] = niches.get(niche, 0) + 1
            
            # Get engagement metrics
            total_reach = sum(p.get('reach', 0) or 0 for p in posts)
            total_engagements = sum(p.get('engagements', 0) or 0 for p in posts)
            total_reactions = sum(p.get('reactions', 0) or 0 for p in posts)
            total_comments = sum(p.get('comments', 0) or 0 for p in posts)
            total_shares = sum(p.get('shares', 0) or 0 for p in posts)
            
            # Get pending content count
            pending_result = self.db.client.table("content").select("id").eq("status", "pending").execute()
            pending_count = len(pending_result.data) if pending_result.data else 0
            
            # Build report
            report = f"""
<b>📊 Africa Lens Daily Report</b>
<b>Date:</b> {today.isoformat()}

<b>📝 Posts Last 24h:</b> {len(posts)}
• French: {french_posts} ({french_posts*100//max(len(posts),1)}%)
• English: {english_posts} ({english_posts*100//max(len(posts),1)}%)

<b>📈 Engagement:</b>
• Reach: {total_reach:,}
• Engagements: {total_engagements:,}
• Reactions: {total_reactions:,}
• Comments: {total_comments:,}
• Shares: {total_shares:,}

<b>🌍 By Country:</b>
"""
            for country, count in sorted(countries.items(), key=lambda x: -x[1])[:5]:
                report += f"• {country}: {count}\n"
            
            report += f"\n<b>📰 By Niche:</b>\n"
            for niche, count in sorted(niches.items(), key=lambda x: -x[1]):
                report += f"• {niche}: {count}\n"
            
            report += f"\n<b>📦 Pending Content:</b> {pending_count}"
            
            # Warnings
            if len(posts) < 20:
                report += f"\n\n⚠️ Low post count (target: 24/day)"
            
            if pending_count < 30:
                report += f"\n⚠️ Low content queue - run scraper"
            
            # Best performing niche
            if niches:
                best_niche = max(niches.items(), key=lambda x: x[1])[0]
                report += f"\n\n🏆 <b>Top Niche:</b> {best_niche}"
            
            report += f"\n\n✅ Bot is running normally"
            
            return report
            
        except Exception as e:
            log_error(f"Report generation error: {e}")
            return f"❌ Error generating report: {e}"
    
    def send_daily_report(self):
        """Generate and send daily report"""
        report = self.generate_daily_report()
        return self.send_message(report)
    
    def send_startup_message(self):
        """Send message when bot starts"""
        message = f"""
🚀 <b>Africa Lens Bot Started</b>
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC

Bot is now running and will post hourly.
Daily reports will be sent at midnight UTC.
"""
        return self.send_message(message)
    
    def send_error_alert(self, error_message):
        """Send error alert"""
        message = f"""
🚨 <b>Africa Lens Bot Error</b>
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC

{error_message}
"""
        return self.send_message(message)
    
    def send_weekly_report(self):
        """Send weekly performance summary"""
        try:
            report_data = self.analytics.get_performance_report(days=7)
            
            if not report_data or isinstance(report_data, str):
                return False
            
            message = f"""
<b>📊 Africa Lens Weekly Report</b>

<b>📝 Overview:</b>
• Total Posts: {report_data['total_posts']}
• Total Reach: {report_data['total_reach']:,}
• Total Engagements: {report_data['total_engagements']:,}
• Avg Reach/Post: {report_data['avg_reach_per_post']:,}

<b>🌍 Top Languages:</b>
"""
            for lang, stats in report_data['by_language'].items():
                avg = stats['reach'] // stats['posts'] if stats['posts'] else 0
                message += f"• {lang.upper()}: {stats['posts']} posts, {avg:,} avg reach\n"
            
            message += f"\n<b>🗺️ Top Countries:</b>\n"
            for country, stats in list(report_data['by_country'].items())[:5]:
                message += f"• {country}: {stats['reach']:,} reach\n"
            
            message += f"\n<b>📰 Best Niches:</b>\n"
            sorted_niches = sorted(report_data['by_niche'].items(), key=lambda x: x[1]['reach'], reverse=True)
            for niche, stats in sorted_niches[:3]:
                message += f"• {niche}: {stats['reach']:,} reach\n"
            
            return self.send_message(message)
            
        except Exception as e:
            log_error(f"Weekly report error: {e}")
            return False


telegram_reporter = TelegramReporter()