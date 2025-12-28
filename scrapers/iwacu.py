from scrapers.base_scraper import BaseScraper

class IWACUScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []

        # Strategy 1: Find div.titraille and get parent with image
        titrailles = soup.select("div.titraille")
        
        for titraille in titrailles[:15]:
            try:
                # Get headline from h2 a
                headline_tag = titraille.select_one("h2 a")
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)

                # Category as summary
                summary = ""
                category_tag = titraille.select_one("h3 a")
                if category_tag:
                    summary = self.clean_text(category_tag.get_text())

                # Image from parent container
                image = ""
                parent = titraille.find_parent("div")
                if parent:
                    img_tag = parent.select_one("img.wp-post-image, img")
                    if img_tag:
                        image = img_tag.get("src") or img_tag.get("data-src") or ""
                        if image.startswith("data:"):
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

        # Strategy 2: Also check article containers as fallback
        if len(articles) < 5:
            article_containers = soup.select("article, .post")
            for item in article_containers[:10]:
                try:
                    headline_tag = item.select_one("h2 a, h3 a")
                    if not headline_tag:
                        continue
                    
                    headline = self.clean_text(headline_tag.get_text())
                    
                    # Skip if already found
                    if any(a["headline"] == headline for a in articles):
                        continue
                    
                    url = headline_tag.get("href", "")
                    url = self.make_absolute_url(url)

                    summary = ""
                    img_tag = item.select_one("img")
                    image = ""
                    if img_tag:
                        image = img_tag.get("src") or img_tag.get("data-src") or ""
                        if not image.startswith("data:"):
                            image = self.make_absolute_url(image)
                        else:
                            image = ""

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