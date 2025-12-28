import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log(message, level="INFO"):
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{date_str}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def log_info(message):
    log(message, "INFO")

def log_error(message):
    log(message, "ERROR")

def log_warning(message):
    log(message, "WARNING")

def log_success(message):
    log(message, "SUCCESS")

def log_scrape(source_name, articles_count):
    log(f"Scraped {articles_count} articles from {source_name}", "SCRAPE")

def log_post(country, language, niche):
    log(f"Posted: {country} | {language} | {niche}", "POST")