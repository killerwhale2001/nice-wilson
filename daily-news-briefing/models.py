"""Shared dataclasses used across all modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsArticle:
    title: str
    url: str
    source: str
    category: str
    published_date: str
    summary: str = ""
    importance_score: float = 0.0
    importance_label: str = ""

    # Basic analyzer fields (used when use_enhanced: false)
    ai_summary: str = ""
    ai_impact: str = ""
    ai_key_points: list[str] = field(default_factory=list)

    # CEO executive briefing fields (used when use_enhanced: true)
    priority: str = ""                          # act | watch | aware
    report_section: str = ""                    # competitive_intel | strategic_opportunity | regulatory_radar | market_signals | industry_pulse
    situation: str = ""                         # what happened (1-2 sentences)
    strategic_implication: str = ""             # what it means for the company
    competitive_implication: str = ""           # impact on competitive position
    recommended_action: str = ""                # what the CEO should do/consider
    key_people: list[str] = field(default_factory=list)   # ["Name — Role"]
    tickers: list[dict] = field(default_factory=list)     # [{ticker, direction, reason}]


@dataclass
class Tweet:
    id: str
    text: str
    created_at: datetime
    author_username: str
    author_name: str
    url: str
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    quote_count: int = 0

    @property
    def engagement_score(self) -> int:
        return self.like_count + self.retweet_count * 2 + self.quote_count * 3
