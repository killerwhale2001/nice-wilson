"""Fetch articles from NewsAPI with 24-36h freshness enforcement.

NewsAPI free tier note:
  - top-headlines: articles are ~24-36h delayed — acceptable for daily briefing
  - top-headlines by source: returns articles years old — NOT used
  - everything + from: blocked on free tier (returns 0) — NOT used
  - Web scraping is the primary source of truly fresh (<24h) content.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from models import NewsArticle

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 5
_MAX_AGE_HOURS = 36  # free tier introduces ~24-36h delay; accept up to 36h


class NewsAPIFetcher:
    def __init__(self, api_key: str, retry_attempts: int = _RETRY_ATTEMPTS, retry_delay: int = _RETRY_DELAY) -> None:
        self.api_key = api_key
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self._session = requests.Session()
        self._session.headers["X-Api-Key"] = api_key

    # ── Public fetch methods ───────────────────────────────────────────────────

    def fetch_by_category(self, category: str, max_articles: int = 5) -> list[NewsArticle]:
        """Fetch top headlines by category, filtered to last 36 hours.

        NewsAPI free tier delays top-headlines by up to 36h — we accept this window
        while still rejecting anything older that slips through.
        """
        # Fetch 3x more to compensate for date filtering drop-off
        params = {"category": category, "language": "en", "pageSize": min(max_articles * 3, 100)}
        raw = self._get("/v2/top-headlines", params)
        filtered = self._filter_age(raw)
        count = len(filtered)
        if count == 0:
            logger.debug("category '%s': 0 articles within %dh (fetched %d)", category, _MAX_AGE_HOURS, len(raw))
        return [self._to_article(a, category) for a in filtered[:max_articles]]

    def fetch_by_keywords(self, query: str, category: str, max_articles: int = 5) -> list[NewsArticle]:
        """Fetch articles matching a keyword query, sorted by recency."""
        from_time = (datetime.now(timezone.utc) - timedelta(hours=_MAX_AGE_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"q": query, "from": from_time, "language": "en", "sortBy": "publishedAt", "pageSize": max_articles}
        raw = self._get("/v2/everything", params)
        if not raw:
            logger.warning(
                "keywords '%s': 0 articles returned — free tier may block 'everything+from'; "
                "web scraping covers fresh content instead.",
                query,
            )
        return [self._to_article(a, category) for a in raw[:max_articles]]

    def fetch_by_source(self, source_id: str, category: str, max_articles: int = 5) -> list[NewsArticle]:
        """Fetch top headlines from a specific NewsAPI source ID, filtered to 36h.

        Note: On the free tier, top-headlines by source can return very old articles.
        Results are strictly filtered — if nothing is recent, an empty list is returned.
        Prefer web scraping for source-specific fresh content.
        """
        params = {"sources": source_id, "pageSize": min(max_articles * 3, 100)}
        raw = self._get("/v2/top-headlines", params)
        filtered = self._filter_age(raw)
        if len(filtered) == 0:
            logger.warning(
                "source '%s': 0 fresh articles within %dh (fetched %d) — "
                "free tier likely caching old content; web scraping covers this source instead.",
                source_id, _MAX_AGE_HOURS, len(raw),
            )
        return [self._to_article(a, category) for a in filtered[:max_articles]]

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"https://newsapi.org{endpoint}"
        for attempt in range(1, self.retry_attempts + 1):
            try:
                resp = self._session.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") != "ok":
                    logger.warning("NewsAPI non-ok: %s", data.get("message"))
                    return []
                return data.get("articles", [])
            except requests.RequestException as exc:
                logger.warning("NewsAPI attempt %d/%d failed: %s", attempt, self.retry_attempts, exc)
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
        logger.error("All NewsAPI attempts exhausted for %s", endpoint)
        return []

    @staticmethod
    def _filter_age(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep only articles published within _MAX_AGE_HOURS."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=_MAX_AGE_HOURS)
        result = []
        for a in articles:
            pub = a.get("publishedAt", "")
            try:
                if datetime.fromisoformat(pub.replace("Z", "+00:00")) >= cutoff:
                    result.append(a)
            except (ValueError, TypeError):
                result.append(a)  # keep if date is missing
        return result

    @staticmethod
    def _to_article(raw: dict[str, Any], category: str) -> NewsArticle:
        source_name = (raw.get("source") or {}).get("name") or "Unknown"
        return NewsArticle(
            title=raw.get("title") or "",
            url=raw.get("url") or "",
            source=source_name,
            category=category,
            published_date=raw.get("publishedAt") or "",
            summary=raw.get("description") or "",
        )
