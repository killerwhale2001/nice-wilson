"""Keyword-based content filter: include/exclude articles by word-boundary matching."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from models import NewsArticle

logger = logging.getLogger(__name__)


@dataclass
class FilterStats:
    total: int = 0
    passed: int = 0
    excluded_by_exclude_list: int = 0
    excluded_by_include_list: int = 0

    @property
    def filtered(self) -> int:
        return self.excluded_by_exclude_list + self.excluded_by_include_list


class ContentFilter:
    def __init__(self, config: dict[str, Any]) -> None:
        cf_cfg = config.get("content_filter", {})
        self.enabled: bool = cf_cfg.get("enabled", True)
        self.case_sensitive: bool = cf_cfg.get("case_sensitive", False)
        include_kws: list[str] = cf_cfg.get("include_keywords", [])
        exclude_kws: list[str] = cf_cfg.get("exclude_keywords", [])
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._include_patterns = [re.compile(rf"\b{re.escape(kw)}\b", flags) for kw in include_kws]
        self._exclude_patterns = [re.compile(rf"\b{re.escape(kw)}\b", flags) for kw in exclude_kws]

    def filter(self, articles: list[NewsArticle]) -> tuple[list[NewsArticle], FilterStats]:
        """Return (kept_articles, stats). Exclude list takes priority over include list."""
        stats = FilterStats(total=len(articles))
        if not self.enabled:
            stats.passed = len(articles)
            return articles, stats

        kept: list[NewsArticle] = []
        for article in articles:
            text = f"{article.title} {article.summary}"
            if self._matches_any(text, self._exclude_patterns):
                stats.excluded_by_exclude_list += 1
                continue
            if self._include_patterns and not self._matches_any(text, self._include_patterns):
                stats.excluded_by_include_list += 1
                continue
            kept.append(article)

        stats.passed = len(kept)
        logger.info(
            "Content filter: %d/%d articles passed (%d excluded by exclude list, %d by include list)",
            stats.passed, stats.total, stats.excluded_by_exclude_list, stats.excluded_by_include_list,
        )
        return kept, stats

    @staticmethod
    def _matches_any(text: str, patterns: list[re.Pattern]) -> bool:
        return any(p.search(text) for p in patterns)
