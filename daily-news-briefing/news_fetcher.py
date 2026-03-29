"""Web-scraping fallback fetcher using BeautifulSoup4."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

from models import NewsArticle

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_CSS_SELECTORS = [
    "article h2 a",
    "article h3 a",
    ".article-title a",
    ".headline a",
    "h2.title a",
    ".story-heading a",
]
_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 5


class NewsFetcher:
    def __init__(self, retry_attempts: int = _RETRY_ATTEMPTS, retry_delay: int = _RETRY_DELAY) -> None:
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self._session = requests.Session()
        self._session.headers["User-Agent"] = _USER_AGENT

    def fetch(self, url: str, category: str, source_name: str, max_articles: int = 5) -> list[NewsArticle]:
        """Scrape article links from a news site homepage."""
        html = self._get_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        links = self._extract_links(soup, url)
        # Scraped articles don't carry publish dates — use scrape time as a proxy.
        # The global 36h filter in briefing_generator keeps these since the date = now().
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        articles: list[NewsArticle] = []
        for title, link in links[:max_articles]:
            articles.append(
                NewsArticle(
                    title=title,
                    url=link,
                    source=source_name,
                    category=category,
                    published_date=today,
                )
            )
        return articles

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_html(self, url: str) -> str | None:
        for attempt in range(1, self.retry_attempts + 1):
            try:
                resp = self._session.get(url, timeout=15)
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as exc:
                logger.warning("Scrape attempt %d/%d for %s failed: %s", attempt, self.retry_attempts, url, exc)
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
        logger.error("All scrape attempts exhausted for %s", url)
        return None

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
        seen: set[str] = set()
        results: list[tuple[str, str]] = []

        # Try specific selectors first
        for selector in _CSS_SELECTORS:
            for tag in soup.select(selector):
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                link = self._resolve(href, base_url)
                if title and link and link not in seen:
                    seen.add(link)
                    results.append((title, link))

        # Generic fallback: any h2/h3 containing an <a>
        if not results:
            for heading in soup.find_all(["h2", "h3"]):
                tag = heading.find("a", href=True)
                if not tag:
                    continue
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                link = self._resolve(href, base_url)
                if title and link and link not in seen:
                    seen.add(link)
                    results.append((title, link))

        return results

    @staticmethod
    def _resolve(href: str, base_url: str) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        from urllib.parse import urljoin
        return urljoin(base_url, href)
