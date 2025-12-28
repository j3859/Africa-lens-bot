from scrapers.base_scraper import BaseScraper

class Burkina24Scraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []

        # Target the actual article containers
        post_items = soup.select(".post-item")

        for item in post_items[:15]:
            try:
                # Headline from h2.post-title a
                headline_tag = item.select_one("h2.post-title a")
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)

                # Summary from p.post-excerpt
                summary = ""
                summary_tag = item.select_one("p.post-excerpt")
                if summary_tag:
                    summary = self.clean_text(summary_tag.get_text())

                # Image from img.wp-post-image with data-lazy-src
                image = ""
                img_tag = item.select_one("img.wp-post-image")
                if img_tag:
                    # Priority: data-lazy-src > data-src > src
                    image = (
                        img_tag.get("data-lazy-src") or 
                        img_tag.get("data-src") or 
                        img_tag.get("src") or 
                        ""
                    )
                    # Skip placeholder SVGs
                    if image.startswith("data:image"):
                        image = ""
                    else:
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