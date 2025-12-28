from scrapers.base_scraper import BaseScraper

class PunchScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []

        # Target article containers
        containers = soup.select("article")

        for item in containers[:15]:
            try:
                # Headline from h2.post-title a
                headline_tag = item.select_one("h2.post-title a, h3.post-title a")
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)

                # Summary - not present in listing
                summary = ""

                # Image from img with data-src (NOT src - that's placeholder)
                image = ""
                img_tag = item.select_one("img.img-lazy-load, img")
                if img_tag:
                    # Priority: data-src over src (src is placeholder)
                    image = img_tag.get("data-src") or ""
                    # Skip if it's the old placeholder
                    if "2021/05" in image or image.startswith("data:"):
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