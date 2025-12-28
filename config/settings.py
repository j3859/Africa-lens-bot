import os
from dotenv import load_dotenv

load_dotenv()

FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_API_VERSION = "v18.0"
FB_BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "AfricaBot/1.0")

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GNEWS_KEY = os.getenv("GNEWS_KEY")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LANGUAGE_SPLIT = {"french": 0.70, "english": 0.30}

NICHE_SPLIT = {"politics": 0.35, "business": 0.25, "tech": 0.20, "entertainment": 0.15, "sports": 0.05}

TIER_1_COUNTRIES = [
    {"name": "Burundi", "code": "BI", "language": "french", "weight": 0.20},
    {"name": "DRC", "code": "CD", "language": "french", "weight": 0.15},
    {"name": "Ivory Coast", "code": "CI", "language": "french", "weight": 0.12},
    {"name": "Kenya", "code": "KE", "language": "english", "weight": 0.10},
    {"name": "Burkina Faso", "code": "BF", "language": "french", "weight": 0.08},
    {"name": "Mali", "code": "ML", "language": "french", "weight": 0.08},
    {"name": "Guinea", "code": "GN", "language": "french", "weight": 0.07},
]

TIER_2_COUNTRIES = [
    {"name": "Nigeria", "code": "NG", "language": "english", "weight": 0.15},
    {"name": "South Africa", "code": "ZA", "language": "english", "weight": 0.12},
    {"name": "Ghana", "code": "GH", "language": "english", "weight": 0.10},
    {"name": "Senegal", "code": "SN", "language": "french", "weight": 0.10},
    {"name": "Cameroon", "code": "CM", "language": "french", "weight": 0.08},
    {"name": "Morocco", "code": "MA", "language": "french", "weight": 0.08},
    {"name": "Ethiopia", "code": "ET", "language": "english", "weight": 0.07},
    {"name": "Tanzania", "code": "TZ", "language": "english", "weight": 0.05},
    {"name": "Uganda", "code": "UG", "language": "english", "weight": 0.05},
    {"name": "Rwanda", "code": "RW", "language": "french", "weight": 0.05},
    {"name": "Algeria", "code": "DZ", "language": "french", "weight": 0.05},
]

IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 630