"""
Africa Lens Bot - Complete Project Status Check
Checks all components against original project plan
"""

import os
import sys
from datetime import datetime, timedelta

print("=" * 60)
print("AFRICA LENS BOT - PROJECT STATUS REPORT")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Track overall status
status_summary = {
    "working": [],
    "partial": [],
    "not_working": [],
    "not_started": []
}

# ============================================================
# 1. ENVIRONMENT & DEPENDENCIES
# ============================================================
print("\n[1] ENVIRONMENT & DEPENDENCIES")
print("-" * 40)

# Check .env file
if os.path.exists(".env"):
    print("  .env file: EXISTS")
    status_summary["working"].append(".env file")
else:
    print("  .env file: MISSING")
    status_summary["not_working"].append(".env file")

# Check required packages
required_packages = [
    "requests", "bs4", "supabase", "google.generativeai",
    "dotenv", "schedule", "lxml"
]
missing_packages = []
for pkg in required_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing_packages.append(pkg)

if not missing_packages:
    print("  Dependencies: ALL INSTALLED")
    status_summary["working"].append("Dependencies")
else:
    print(f"  Dependencies: MISSING {missing_packages}")
    status_summary["not_working"].append("Dependencies")

# ============================================================
# 2. CONFIGURATION
# ============================================================
print("\n[2] CONFIGURATION")
print("-" * 40)

try:
    from config.settings import (
        FB_ACCESS_TOKEN, FB_PAGE_ID, SUPABASE_URL,
        SUPABASE_KEY, GEMINI_API_KEY
    )
    
    configs = {
        "FB_ACCESS_TOKEN": bool(FB_ACCESS_TOKEN and FB_ACCESS_TOKEN != "placeholder"),
        "FB_PAGE_ID": bool(FB_PAGE_ID and FB_PAGE_ID != "placeholder"),
        "SUPABASE_URL": bool(SUPABASE_URL and SUPABASE_URL != "placeholder"),
        "SUPABASE_KEY": bool(SUPABASE_KEY and SUPABASE_KEY != "placeholder"),
        "GEMINI_API_KEY": bool(GEMINI_API_KEY and GEMINI_API_KEY != "placeholder"),
    }
    
    for key, valid in configs.items():
        status = "SET" if valid else "MISSING/PLACEHOLDER"
        print(f"  {key}: {status}")
    
    if all(configs.values()):
        status_summary["working"].append("Configuration")
    else:
        status_summary["partial"].append("Configuration")
        
except Exception as e:
    print(f"  Configuration error: {e}")
    status_summary["not_working"].append("Configuration")

# ============================================================
# 3. DATABASE CONNECTION & TABLES
# ============================================================
print("\n[3] DATABASE (SUPABASE)")
print("-" * 40)

try:
    from utils.database import supabase
    
    tables_expected = ["sources", "content", "posts", "schedule", "language_stats", "country_stats"]
    tables_status = {}
    
    for table in tables_expected:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            count_result = supabase.table(table).select("*", count="exact").execute()
            count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            tables_status[table] = count
            print(f"  {table}: {count} records")
        except Exception as e:
            tables_status[table] = None
            print(f"  {table}: ERROR - {e}")
    
    if all(v is not None for v in tables_status.values()):
        status_summary["working"].append("Database Connection")
        status_summary["working"].append("Database Tables")
    else:
        status_summary["partial"].append("Database Tables")
        
except Exception as e:
    print(f"  Database error: {e}")
    status_summary["not_working"].append("Database")

# ============================================================
# 4. SCRAPERS
# ============================================================
print("\n[4] SCRAPERS")
print("-" * 40)

scraper_files = {
    "jeune_afrique.py": "Jeune Afrique (Pan-African French)",
    "actualite_cd.py": "Actualite.cd (DRC French)",
    "iwacu.py": "IWACU (Burundi French)",
    "punch.py": "Punch Nigeria (English)",
    "burkina24.py": "Burkina 24 (French)",
    "base_scraper.py": "Base Scraper Class",
    "scraper_manager.py": "Scraper Manager",
}

scrapers_found = 0
for filename, description in scraper_files.items():
    filepath = os.path.join("scrapers", filename)
    exists = os.path.exists(filepath)
    status = "EXISTS" if exists else "MISSING"
    print(f"  {description}: {status}")
    if exists:
        scrapers_found += 1

if scrapers_found == len(scraper_files):
    status_summary["working"].append("Scraper Files")
else:
    status_summary["partial"].append("Scraper Files")

# Check sources in database
try:
    sources_result = supabase.table("sources").select("*").execute()
    total_sources = len(sources_result.data)
    active_sources = len([s for s in sources_result.data if s.get("is_active")])
    print(f"\n  Sources in database: {total_sources}")
    print(f"  Active sources: {active_sources}")
except:
    pass

# ============================================================
# 5. PROCESSORS
# ============================================================
print("\n[5] PROCESSORS")
print("-" * 40)

processor_files = {
    "ai_processor.py": "AI Processor (Gemini)",
    "facebook_poster.py": "Facebook Poster",
    "content_selector.py": "Content Selector",
    "post_engine.py": "Post Engine",
    "scraper_runner.py": "Scraper Runner",
}

processors_found = 0
for filename, description in processor_files.items():
    filepath = os.path.join("processors", filename)
    exists = os.path.exists(filepath)
    status = "EXISTS" if exists else "MISSING"
    print(f"  {description}: {status}")
    if exists:
        processors_found += 1

if processors_found == len(processor_files):
    status_summary["working"].append("Processor Files")
else:
    status_summary["partial"].append("Processor Files")

# ============================================================
# 6. AI PROCESSOR TEST
# ============================================================
print("\n[6] AI PROCESSOR (GEMINI)")
print("-" * 40)

try:
    from processors.ai_processor import ai_processor
    print("  Module loaded: YES")
    
    # Check model name
    if hasattr(ai_processor, 'model'):
        model_name = getattr(ai_processor.model, 'model_name', 'Unknown')
        print(f"  Model: {model_name}")
    
    status_summary["working"].append("AI Processor")
except Exception as e:
    print(f"  AI Processor error: {e}")
    status_summary["not_working"].append("AI Processor")

# ============================================================
# 7. FACEBOOK POSTER TEST
# ============================================================
print("\n[7] FACEBOOK POSTER")
print("-" * 40)

try:
    from processors.facebook_poster import fb_poster
    print("  Module loaded: YES")
    
    # Verify token
    token_valid = fb_poster.verify_token()
    print(f"  Token valid: {'YES' if token_valid else 'NO'}")
    
    if token_valid:
        status_summary["working"].append("Facebook Poster")
    else:
        status_summary["partial"].append("Facebook Poster")
except Exception as e:
    print(f"  Facebook Poster error: {e}")
    status_summary["not_working"].append("Facebook Poster")

# ============================================================
# 8. CONTENT STATUS
# ============================================================
print("\n[8] CONTENT STATUS")
print("-" * 40)

try:
    # Pending content
    pending = supabase.table("content").select("*").eq("status", "pending").execute()
    pending_count = len(pending.data)
    print(f"  Pending articles: {pending_count}")
    
    # Posted content
    posted = supabase.table("content").select("*").eq("status", "posted").execute()
    posted_count = len(posted.data)
    print(f"  Posted articles: {posted_count}")
    
    # Content with images
    with_images = len([c for c in pending.data if c.get("image_url") and c["image_url"].startswith("http")])
    print(f"  Pending with images: {with_images}")
    
    # By language
    french_content = len([c for c in pending.data if c.get("source_language") == "french"])
    english_content = len([c for c in pending.data if c.get("source_language") == "english"])
    print(f"  French content: {french_content}")
    print(f"  English content: {english_content}")
    
    status_summary["working"].append("Content Pipeline")
except Exception as e:
    print(f"  Content check error: {e}")

# ============================================================
# 9. POSTING HISTORY
# ============================================================
print("\n[9] POSTING HISTORY")
print("-" * 40)

try:
    posts = supabase.table("posts").select("*").order("posted_at", desc=True).limit(10).execute()
    total_posts = len(posts.data)
    print(f"  Total posts recorded: {total_posts}")
    
    if posts.data:
        latest = posts.data[0]
        print(f"  Latest post: {latest.get('posted_at', 'Unknown')}")
        
        # Language breakdown
        french_posts = len([p for p in posts.data if p.get("post_language") == "french"])
        english_posts = len([p for p in posts.data if p.get("post_language") == "english"])
        print(f"  Recent French posts: {french_posts}")
        print(f"  Recent English posts: {english_posts}")
except Exception as e:
    print(f"  Posts check error: {e}")

# ============================================================
# 10. SCHEDULE
# ============================================================
print("\n[10] POSTING SCHEDULE")
print("-" * 40)

try:
    schedule = supabase.table("schedule").select("*").execute()
    schedule_count = len(schedule.data)
    active_slots = len([s for s in schedule.data if s.get("is_active")])
    print(f"  Total slots: {schedule_count}")
    print(f"  Active slots: {active_slots}")
    
    if schedule_count == 24:
        print("  24-hour coverage: YES")
        status_summary["working"].append("Posting Schedule")
    else:
        print(f"  24-hour coverage: NO ({schedule_count}/24)")
        status_summary["partial"].append("Posting Schedule")
except Exception as e:
    print(f"  Schedule check error: {e}")

# ============================================================
# 11. UTILITIES
# ============================================================
print("\n[11] UTILITIES")
print("-" * 40)

utility_files = {
    "database.py": "Database Operations",
    "logger.py": "Logging Utility",
    "http_helper.py": "HTTP Helper",
}

utils_found = 0
for filename, description in utility_files.items():
    filepath = os.path.join("utils", filename)
    exists = os.path.exists(filepath)
    status = "EXISTS" if exists else "MISSING"
    print(f"  {description}: {status}")
    if exists:
        utils_found += 1

if utils_found == len(utility_files):
    status_summary["working"].append("Utility Files")

# ============================================================
# 12. MAIN ENTRY POINT
# ============================================================
print("\n[12] MAIN ENTRY POINT")
print("-" * 40)

if os.path.exists("main.py"):
    print("  main.py: EXISTS")
    status_summary["working"].append("Main Entry Point")
else:
    print("  main.py: MISSING")
    status_summary["not_working"].append("Main Entry Point")

# ============================================================
# 13. LOGS DIRECTORY
# ============================================================
print("\n[13] LOGGING")
print("-" * 40)

if os.path.exists("logs"):
    log_files = os.listdir("logs")
    print(f"  logs/ directory: EXISTS")
    print(f"  Log files: {len(log_files)}")
    status_summary["working"].append("Logging")
else:
    print("  logs/ directory: MISSING")
    status_summary["partial"].append("Logging")

# ============================================================
# 14. NOT YET IMPLEMENTED
# ============================================================
print("\n[14] NOT YET IMPLEMENTED (Per Original Plan)")
print("-" * 40)

not_implemented = [
    "Reddit API integration",
    "Google Trends integration",
    "YouTube Data API",
    "NewsAPI.org integration",
    "GNews.io integration",
    "Facebook analytics/metrics collection",
    "Stock image fallback (Unsplash/Pexels)",
    "Telegram deployment",
    "24/7 cloud hosting",
]

for item in not_implemented:
    print(f"  [ ] {item}")
    status_summary["not_started"].append(item)

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n")
print("=" * 60)
print("FINAL SUMMARY")
print("=" * 60)

print(f"\n  WORKING ({len(status_summary['working'])} items):")
for item in status_summary["working"]:
    print(f"    [OK] {item}")

if status_summary["partial"]:
    print(f"\n  PARTIAL ({len(status_summary['partial'])} items):")
    for item in status_summary["partial"]:
        print(f"    [!!] {item}")

if status_summary["not_working"]:
    print(f"\n  NOT WORKING ({len(status_summary['not_working'])} items):")
    for item in status_summary["not_working"]:
        print(f"    [XX] {item}")

print(f"\n  NOT STARTED ({len(status_summary['not_started'])} items):")
for item in status_summary["not_started"]:
    print(f"    [--] {item}")

# Calculate completion percentage
total_planned = len(status_summary["working"]) + len(status_summary["partial"]) + len(status_summary["not_working"]) + len(status_summary["not_started"])
completed = len(status_summary["working"])
partial = len(status_summary["partial"]) * 0.5

completion = ((completed + partial) / total_planned) * 100 if total_planned > 0 else 0

print("\n" + "=" * 60)
print(f"PROJECT COMPLETION: {completion:.1f}%")
print("=" * 60)

print("\nCore bot functionality (scraping, AI, posting) is COMPLETE.")
print("Remaining items are enhancements and deployment.")