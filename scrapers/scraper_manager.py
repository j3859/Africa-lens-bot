from scrapers.jeune_afrique import JeuneAfriqueScraper
from scrapers.actualite_cd import ActualiteCDScraper
from scrapers.iwacu import IWACUScraper
from scrapers.punch import PunchScraper
from scrapers.burkina24 import Burkina24Scraper
from scrapers.abidjan_net import AbidjanNetScraper
from scrapers.fratmat import FratmatScraper
from scrapers.allafrica import AllAfricaScraper
from scrapers.maliactu import MaliActuScraper
from scrapers.seneweb import SenewebScraper
from scrapers.generic_scraper import GenericScraper
from scrapers.api_scrapers import GNewsAPIScraper, YouTubeAPIScraper, NewsAPIScraper, GoogleTrendsScraper
from utils.logger import log_warning

SCRAPER_MAP = {
    # Custom web scrapers
    "Jeune Afrique": JeuneAfriqueScraper,
    "Actualite.cd": ActualiteCDScraper,
    "IWACU": IWACUScraper,
    "Punch": PunchScraper,
    "Burkina 24": Burkina24Scraper,
    "Abidjan.net": AbidjanNetScraper,
    "Fratmat": FratmatScraper,
    "AllAfrica": AllAfricaScraper,
    "Maliactu": MaliActuScraper,
    "Seneweb": SenewebScraper,
    # API scrapers
    "GNews": GNewsAPIScraper,
    "YouTube": YouTubeAPIScraper,
    "NewsAPI": NewsAPIScraper,
    "Google Trends": GoogleTrendsScraper,
}

def get_scraper(source):
    scraper_class = SCRAPER_MAP.get(source["name"], GenericScraper)

    return scraper_class(
        source_id=source["id"],
        name=source["name"],
        url=source["url"],
        country=source["country"],
        country_code=source["country_code"],
        language=source["language"],
        niche=source["niche"]
    )