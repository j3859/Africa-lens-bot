from scrapers.base_scraper import BaseScraper

class FratmatScraper(BaseScraper):
    def parse_articles(self, html):
        soup = self.get_soup(html)
        articles = []
        seen_urls = set()

        # Target ALL article container types
        selectors = [
            "div.relative.content",
            "div.article-one",
            "div.article-two",
            "div.article-div2",
            "div.article-div3",
            "div.hp_main_article",
            "div[class*='article-']",
            "article",
            "div.item",
            "div.col-md-3",
            "div.col-md-4",
            "div.col-12"
        ]
        
        containers = []
        for selector in selectors:
            containers.extend(soup.select(selector))

        for item in containers:
            if len(articles) >= 15:
                break

            try:
                # Find headline link
                headline_tag = item.select_one("a.article-title")
                if not headline_tag:
                    # Fallback: find link with /article/ in href
                    for a in item.select("a[href*='/article/']"):
                        text = a.get_text().strip()
                        if len(text) > 20:
                            headline_tag = a
                            break
                
                if not headline_tag:
                    continue
                
                headline = self.clean_text(headline_tag.get_text())
                if len(headline) < 20:
                    continue
                    
                url = headline_tag.get("href", "")
                url = self.make_absolute_url(url)
                
                # Skip duplicates
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                summary = ""

                # Image from img.lazy with data-src
                image = ""
                img_tag = item.select_one("img.lazy, img")
                if img_tag:
                    image = img_tag.get("data-src") or img_tag.get("src") or ""
                    if image.startswith("data:") or "no-image" in image:
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