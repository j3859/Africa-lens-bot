import requests
import os
import tempfile
from bs4 import BeautifulSoup
from utils.logger import log_warning

# Default headers that work for most sites
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Sites that need Googlebot header
GOOGLEBOT_SITES = [
    'addisstandard.com',
]

GOOGLEBOT_HEADERS = {
    'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
}

def get_headers_for_url(url):
    """Get appropriate headers for a URL"""
    for site in GOOGLEBOT_SITES:
        if site in url:
            return GOOGLEBOT_HEADERS
    return DEFAULT_HEADERS

def fetch_page(url, timeout=15, max_retries=3):
    """Fetch a web page with appropriate headers"""
    headers = get_headers_for_url(url)
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=timeout, 
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                log_warning(f"Access denied (403) for {url}")
                return None
            else:
                log_warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except requests.exceptions.Timeout:
            log_warning(f"Timeout fetching {url} (attempt {attempt}/{max_retries})")
        except requests.exceptions.ConnectionError:
            log_warning(f"Connection error fetching {url} (attempt {attempt}/{max_retries})")
        except Exception as e:
            log_warning(f"Error fetching {url}: {e}")
            return None
    
    return None

def download_image(url, timeout=10):
    """Download an image and return the local file path"""
    if not url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        if response.status_code != 200:
            log_warning(f"Failed to download image: HTTP {response.status_code}")
            return None
        
        # Determine file extension
        content_type = response.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'webp' in content_type:
            ext = '.webp'
        else:
            ext = '.jpg'  # Default
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        
        temp_file.close()
        return temp_file.name
        
    except Exception as e:
        log_warning(f"Error downloading image {url}: {e}")
        return None

def extract_og_image(html):
    """Extract Open Graph image from HTML"""
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Try og:image first
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            return og_image.get("content", "")
        
        # Try twitter:image
        twitter_image = soup.select_one('meta[name="twitter:image"]')
        if twitter_image:
            return twitter_image.get("content", "")
        
        return ""
    except Exception:
        return ""

def extract_meta_description(html):
    """Extract meta description from HTML"""
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Try og:description first
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            return og_desc.get("content", "")
        
        # Try regular meta description
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc:
            return meta_desc.get("content", "")
        
        return ""
    except Exception:
        return ""