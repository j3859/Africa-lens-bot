from scrapers.base_scraper import BaseScraper

class ActualiteCDScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []

        # Target views-row containers
        containers = soup.select(".views-row")

        for item in containers[:15]:
            try:
                # Headline from h4 a or h3 a
                headline_tag = item.select_one("h4 a, h3 a, h2 a")
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)

                # Summary - category can serve as context
                summary = ""
                category_tag = item.select_one("span a, .color1 a")
                if category_tag:
                    summary = self.clean_text(category_tag.get_text())

                # Image from img with src (relative URL)
                image = ""
                img_tag = item.select_one("img")
                if img_tag:
                    image = img_tag.get("src") or ""
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