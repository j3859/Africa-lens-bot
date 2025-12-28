import os
import requests
from datetime import datetime, timedelta
from utils.database import Database
from utils.logger import log_info, log_error, log_success, log_warning

class FacebookAnalytics:
    """Fetch and analyze Facebook post performance"""
    
    def __init__(self):
        self.access_token = os.getenv("FB_ACCESS_TOKEN", "")
        self.page_id = os.getenv("FB_PAGE_ID", "")
        self.db = Database()
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def get_post_insights(self, post_id):
        """Fetch insights for a specific post"""
        try:
            # Get basic post metrics
            url = f"{self.base_url}/{post_id}"
            params = {
                "fields": "id,message,created_time,shares,likes.summary(true),comments.summary(true)",
                "access_token": self.access_token
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                log_warning(f"Failed to get post {post_id}: {response.status_code}")
                return None
            
            data = response.json()
            
            # Get post insights (reach, impressions, engagement)
            insights_url = f"{self.base_url}/{post_id}/insights"
            insights_params = {
                "metric": "post_impressions,post_impressions_unique,post_engaged_users,post_clicks",
                "access_token": self.access_token
            }
            
            insights_response = requests.get(insights_url, params=insights_params, timeout=15)
            
            insights = {}
            if insights_response.status_code == 200:
                insights_data = insights_response.json()
                for item in insights_data.get("data", []):
                    metric_name = item.get("name", "")
                    values = item.get("values", [])
                    if values:
                        insights[metric_name] = values[0].get("value", 0)
            
            return {
                "post_id": post_id,
                "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
                "shares": data.get("shares", {}).get("count", 0) if data.get("shares") else 0,
                "impressions": insights.get("post_impressions", 0),
                "reach": insights.get("post_impressions_unique", 0),
                "engagements": insights.get("post_engaged_users", 0),
                "clicks": insights.get("post_clicks", 0),
            }
            
        except Exception as e:
            log_error(f"Error fetching insights for {post_id}: {e}")
            return None
    
    def update_post_metrics(self, post_id, content_id):
        """Update metrics for a post in database"""
        insights = self.get_post_insights(post_id)
        
        if not insights:
            return False
        
        try:
            self.db.client.table("posts").update({
                "reach": insights.get("reach", 0),
                "impressions": insights.get("impressions", 0),
                "engagements": insights.get("engagements", 0),
                "reactions": insights.get("likes", 0),
                "comments": insights.get("comments", 0),
                "shares": insights.get("shares", 0),
                "metrics_updated_at": datetime.utcnow().isoformat()
            }).eq("facebook_post_id", post_id).execute()
            
            return True
        except Exception as e:
            log_error(f"Error updating metrics: {e}")
            return False
    
    def update_all_recent_posts(self, hours=24):
        """Update metrics for all posts from last N hours"""
        try:
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            result = self.db.client.table("posts").select(
                "id, facebook_post_id, content_id"
            ).gte("posted_at", cutoff).execute()
            
            posts = result.data if result.data else []
            
            log_info(f"Updating metrics for {len(posts)} posts...")
            
            updated = 0
            for post in posts:
                fb_post_id = post.get("facebook_post_id")
                if fb_post_id:
                    success = self.update_post_metrics(fb_post_id, post.get("content_id"))
                    if success:
                        updated += 1
            
            log_success(f"Updated metrics for {updated}/{len(posts)} posts")
            return updated
            
        except Exception as e:
            log_error(f"Error updating recent posts: {e}")
            return 0
    
    def get_performance_report(self, days=7):
        """Generate performance report for last N days"""
        try:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.db.client.table("posts").select(
                "id, post_language, target_country, niche, reach, impressions, engagements, reactions, comments, shares, posted_at"
            ).gte("posted_at", cutoff).execute()
            
            posts = result.data if result.data else []
            
            if not posts:
                return "No posts in the last {days} days"
            
            # Aggregate by language
            lang_stats = {}
            for post in posts:
                lang = post.get("post_language", "unknown")
                if lang not in lang_stats:
                    lang_stats[lang] = {"posts": 0, "reach": 0, "engagements": 0}
                lang_stats[lang]["posts"] += 1
                lang_stats[lang]["reach"] += post.get("reach", 0) or 0
                lang_stats[lang]["engagements"] += post.get("engagements", 0) or 0
            
            # Aggregate by country
            country_stats = {}
            for post in posts:
                country = post.get("target_country", "unknown")
                if country not in country_stats:
                    country_stats[country] = {"posts": 0, "reach": 0, "engagements": 0}
                country_stats[country]["posts"] += 1
                country_stats[country]["reach"] += post.get("reach", 0) or 0
                country_stats[country]["engagements"] += post.get("engagements", 0) or 0
            
            # Aggregate by niche
            niche_stats = {}
            for post in posts:
                niche = post.get("niche", "unknown")
                if niche not in niche_stats:
                    niche_stats[niche] = {"posts": 0, "reach": 0, "engagements": 0}
                niche_stats[niche]["posts"] += 1
                niche_stats[niche]["reach"] += post.get("reach", 0) or 0
                niche_stats[niche]["engagements"] += post.get("engagements", 0) or 0
            
            # Calculate totals
            total_reach = sum(p.get("reach", 0) or 0 for p in posts)
            total_engagements = sum(p.get("engagements", 0) or 0 for p in posts)
            total_reactions = sum(p.get("reactions", 0) or 0 for p in posts)
            total_comments = sum(p.get("comments", 0) or 0 for p in posts)
            total_shares = sum(p.get("shares", 0) or 0 for p in posts)
            
            report = {
                "period_days": days,
                "total_posts": len(posts),
                "total_reach": total_reach,
                "total_engagements": total_engagements,
                "total_reactions": total_reactions,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "avg_reach_per_post": total_reach // len(posts) if posts else 0,
                "avg_engagements_per_post": total_engagements // len(posts) if posts else 0,
                "by_language": lang_stats,
                "by_country": dict(sorted(country_stats.items(), key=lambda x: x[1]["reach"], reverse=True)[:10]),
                "by_niche": niche_stats,
            }
            
            return report
            
        except Exception as e:
            log_error(f"Error generating report: {e}")
            return None
    
    def get_best_performing_content(self, days=7, limit=10):
        """Get top performing posts"""
        try:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.db.client.table("posts").select(
                "id, post_text, post_language, target_country, niche, reach, engagements, reactions, comments, shares, posted_at"
            ).gte("posted_at", cutoff).order("reach", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            log_error(f"Error getting best content: {e}")
            return []
    
    def print_report(self, days=7):
        """Print formatted performance report"""
        report = self.get_performance_report(days)
        
        if not report or isinstance(report, str):
            print(report or "No data available")
            return
        
        print("="*60)
        print(f"PERFORMANCE REPORT - Last {days} Days")
        print("="*60)
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Posts: {report['total_posts']}")
        print(f"   Total Reach: {report['total_reach']:,}")
        print(f"   Total Engagements: {report['total_engagements']:,}")
        print(f"   Avg Reach/Post: {report['avg_reach_per_post']:,}")
        print(f"   Reactions: {report['total_reactions']:,} | Comments: {report['total_comments']:,} | Shares: {report['total_shares']:,}")
        
        print(f"\n🌍 BY LANGUAGE:")
        for lang, stats in report['by_language'].items():
            avg_reach = stats['reach'] // stats['posts'] if stats['posts'] else 0
            print(f"   {lang.upper()}: {stats['posts']} posts, {stats['reach']:,} reach, {avg_reach:,} avg")
        
        print(f"\n🗺️  TOP COUNTRIES:")
        for country, stats in list(report['by_country'].items())[:5]:
            avg_reach = stats['reach'] // stats['posts'] if stats['posts'] else 0
            print(f"   {country}: {stats['posts']} posts, {stats['reach']:,} reach, {avg_reach:,} avg")
        
        print(f"\n📰 BY NICHE:")
        for niche, stats in report['by_niche'].items():
            avg_reach = stats['reach'] // stats['posts'] if stats['posts'] else 0
            print(f"   {niche}: {stats['posts']} posts, {stats['reach']:,} reach, {avg_reach:,} avg")
        
        print("\n" + "="*60)


fb_analytics = FacebookAnalytics()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    analytics = FacebookAnalytics()
    
    print("Testing Facebook Analytics...")
    print()
    
    # Update recent posts
    analytics.update_all_recent_posts(hours=48)
    
    # Print report
    analytics.print_report(days=7)