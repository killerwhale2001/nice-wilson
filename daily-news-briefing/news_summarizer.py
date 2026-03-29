"""Fallback summarizer: extract summary from HTML meta tags or first paragraph."""

from __future__ import annotations

import logging
import re

import requests
from bs4 import BeautifulSoup

from models import NewsArticle

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_META_SELECTORS = [
    ("meta", {"name": "description"}),
    ("meta", {"property": "og:description"}),
    ("meta", {"name": "twitter:description"}),
]
_MIN_PARAGRAPH_LENGTH = 50
_MAX_SUMMARY_LENGTH = 200


class NewsSummarizer:
    def __init__(self, max_length: int = _MAX_SUMMARY_LENGTH) -> None:
        self.max_length = max_length
        self._session = requests.Session()
        self._session.headers["User-Agent"] = _USER_AGENT

    def summarize(self, article: NewsArticle) -> NewsArticle:
        """Fetch article page and populate article.summary if not already set."""
        if article.summary:
            return article  # already has a summary

        html = self._fetch(article.url)
        if not html:
            return article

        soup = BeautifulSoup(html, "lxml")
        summary = self._from_meta(soup) or self._from_paragraph(soup)
        if summary:
            article.summary = self._truncate(summary)
        return article

    # ── Extraction helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _from_meta(soup: BeautifulSoup) -> str:
        for tag, attrs in _META_SELECTORS:
            el = soup.find(tag, attrs)
            if el and el.get("content"):
                return str(el["content"]).strip()
        return ""

    @staticmethod
    def _from_paragraph(soup: BeautifulSoup) -> str:
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) >= _MIN_PARAGRAPH_LENGTH:
                return text
        return ""

    def _truncate(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= self.max_length:
            return text
        return text[: self.max_length - 1].rsplit(" ", 1)[0] + "…"

    def _fetch(self, url: str) -> str | None:
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            logger.debug("Summarizer fetch failed for %s: %s", url, exc)
            return None
