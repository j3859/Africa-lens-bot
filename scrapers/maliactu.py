from scrapers.base_scraper import BaseScraper

class MaliActuScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []

        containers = soup.select("li")

        for item in containers:
            if len(articles) >= 15:
                break
                
            try:
                headline_tag = item.select_one("a")
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                if len(headline) < 25:
                    continue
                    
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)

                summary = ""
                summary_tag = item.select_one("p, .excerpt")
                if summary_tag:
                    summary = self.clean_text(summary_tag.get_text())

                image = ""
                img_tag = item.select_one("img")
                if img_tag:
                    image = img_tag.get("data-src") or img_tag.get("src") or ""
                    if image.startswith("data:"):
                        image = ""
                    elif image:
                        image = self.make_absolute_url(image)

                if headline and len(headline) > 15:
                    articles.append({
                        "headline": headline,
                        "summary": summary[:500],
                        "url": url,
                        "image": image
                    })
            except Exception:
                continue

        return articles