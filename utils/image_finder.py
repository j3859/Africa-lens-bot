import requests
from config.settings import PEXELS_API_KEY, UNSPLASH_ACCESS_KEY
from utils.logger import log_error, log_info

def get_stock_image(query):
    """
    Search Pexels or Unsplash for a relevant stock image based on query.
    Returns URL of proper aspect ratio image or None.
    """
    if not query:
        return None
        
    # Try Pexels first (high quality, good search)
    if PEXELS_API_KEY and PEXELS_API_KEY != "your_pexels_key_here":
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": query, "per_page": 1, "orientation": "landscape"}
            
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            if "photos" in data and len(data["photos"]) > 0:
                # Prefer 'large2x' or 'landscape'
                return data["photos"][0]["src"]["large2x"]
        except Exception as e:
            log_error(f"Pexels search failed: {e}")

    # Fallback to Unsplash (if key exists)
    if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_key_here":
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            params = {"query": query, "per_page": 1, "orientation": "landscape"}
            
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            if "results" in data and len(data["results"]) > 0:
                return data["results"][0]["urls"]["regular"]
        except Exception as e:
            log_error(f"Unsplash search failed: {e}")
    
    log_warning(f"No stock image found for query: {query}")

    return None
