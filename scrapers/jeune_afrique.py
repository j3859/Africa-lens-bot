from scrapers.base_scraper import BaseScraper

class JeuneAfriqueScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []

        # Only target article containers that have images
        # Exclude: thumbnail--sm, thumbnail--x-sm (text-only)
        selectors = [
            "article.thumbnail--lg",
            "article.thumbnail--lg-title",
            "article.thumbnail--lg-trans",
            "article.thumbnail--md-title",
            "article.thumbnail--md-trans",
            "article.thumbnail--folder",
        ]
        
        containers = []
        for selector in selectors:
            containers.extend(soup.select(selector))

        for item in containers[:15]:
            try:
                # Headline from h4, h3, or h2
                headline_tag = item.select_one("h4.thumbnail__title a, h3.thumbnail__title a, h2 a, h3 a, h4 a")
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)

                # Summary from excerpt if available
                summary = ""
                summary_tag = item.select_one(".thumbnail__excerpt, .excerpt, p")
                if summary_tag:
                    summary = self.clean_text(summary_tag.get_text())

                # Image from img tag
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