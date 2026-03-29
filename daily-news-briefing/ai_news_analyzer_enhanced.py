"""CEO-level executive briefing analyzer: strategic intelligence, not summaries."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from models import NewsArticle

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {"act": 0, "watch": 1, "aware": 2}
_SECTION_ORDER = {
    "competitive_intel": 0,
    "strategic_opportunity": 1,
    "regulatory_radar": 2,
    "market_signals": 3,
    "industry_pulse": 4,
}


class AINewsAnalyzerEnhanced:
    def __init__(self, config: dict[str, Any]) -> None:
        ai_cfg = config.get("ai_analysis", {})
        self.client = OpenAI(api_key=ai_cfg.get("api_key"))
        self.model = ai_cfg.get("model", "gpt-4o-mini")
        self.temperature = ai_cfg.get("temperature", 0.4)
        self.max_tokens = ai_cfg.get("max_tokens", 600)
        self.custom_instructions: str = ai_cfg.get("custom_instructions", "")
        self.focus_areas: list[str] = ai_cfg.get("focus_areas", [])

    def analyze_article(self, article: NewsArticle) -> NewsArticle:
        """Per-article CEO-level analysis: priority, section, situation, implications, action."""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._article_prompt(article)},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            article.priority = data.get("priority", "aware")
            article.report_section = data.get("section", "industry_pulse")
            article.situation = data.get("situation", "")
            article.strategic_implication = data.get("strategic_implication", "")
            article.competitive_implication = data.get("competitive_implication", "")
            article.recommended_action = data.get("recommended_action", "")
            article.key_people = data.get("key_people", [])
            article.tickers = data.get("tickers", [])
        except Exception as exc:
            logger.warning("Article analysis failed for '%s': %s", article.title, exc)
        return article

    def generate_board_summary(self, articles: list[NewsArticle]) -> str:
        """2-3 sentences you'd open a board meeting with today."""
        if not articles:
            return ""
        context = "\n".join(
            f"- [{a.priority.upper()}] {a.title}: {a.strategic_implication}"
            for a in articles if a.strategic_implication
        )
        if not context:
            return ""
        prompt = (
            f"Today's intelligence briefing covers these developments:\n{context}\n\n"
            "Write 2-3 sentences that a CEO would use to open a board meeting today. "
            "Be direct, strategic, and confident. Focus on the biggest strategic shift "
            "and what it means for the company's position. No hedging, no filler."
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.5,
                max_tokens=200,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.warning("Board summary failed: %s", exc)
            return ""

    def generate_tldr(self, articles: list[NewsArticle]) -> list[str]:
        """5 bullets — full briefing in 30 seconds."""
        if not articles:
            return []
        context = "\n".join(
            f"- [{a.priority.upper()}] {a.title} — {a.strategic_implication or a.situation}"
            for a in articles
        )
        prompt = (
            f"Today's intelligence:\n{context}\n\n"
            "Write exactly 5 punchy one-sentence bullets covering the most important "
            "developments a tech CEO must know today. Lead each with the most critical fact. "
            "Be sharp and direct — no fluff. "
            'Return JSON: {"bullets": ["...", "...", "...", "...", "..."]}'
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.4,
                max_tokens=300,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            return data.get("bullets", [])
        except Exception as exc:
            logger.warning("TL;DR failed: %s", exc)
            return []

    def generate_market_watch(self, articles: list[NewsArticle]) -> list[dict[str, Any]]:
        """Aggregate ticker signals from all articles."""
        ticker_map: dict[str, dict[str, Any]] = {}
        for article in articles:
            for t in article.tickers:
                ticker = t.get("ticker", "").upper()
                if not ticker:
                    continue
                if ticker not in ticker_map:
                    ticker_map[ticker] = {"ticker": ticker, "direction": t.get("direction", "neutral"), "reasons": []}
                reason = t.get("reason", "")
                if reason:
                    ticker_map[ticker]["reasons"].append(reason)
        # Sort: bearish first (most urgent), then bullish, then neutral
        order = {"bearish": 0, "bullish": 1, "neutral": 2}
        return sorted(ticker_map.values(), key=lambda x: order.get(x.get("direction", "neutral"), 2))

    def generate_what_to_watch(self, articles: list[NewsArticle]) -> list[str]:
        """Upcoming events and decisions requiring CEO awareness."""
        if not articles:
            return []
        context = "\n".join(
            f"- {a.title}: {a.situation or a.summary}"
            for a in articles if a.situation or a.summary
        )
        if not context:
            return []
        prompt = (
            f"Based on today's briefing:\n{context}\n\n"
            "List up to 5 specific upcoming events a tech CEO must track — earnings, "
            "regulatory decisions, product launches, Fed meetings, competitive announcements. "
            "Be specific with company names and dates where known. "
            'Return JSON: {"items": ["...", "..."]}'
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                max_tokens=250,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            return data.get("items", [])
        except Exception as exc:
            logger.warning("What to Watch failed: %s", exc)
            return []

    # ── Prompt builders ────────────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        base = (
            "You are the Chief of Staff to the CEO of the world's leading technology company. "
            "You prepare a confidential daily intelligence briefing — written with the precision "
            "of a classified briefing document, not a tech blog. "
            "Every analysis must answer: 'What does this mean for our company, our competitors, "
            "and what — if anything — should the CEO do about it?' "
            "Be direct. No filler. No passive voice. Assume the CEO reads fast and thinks in strategy."
        )
        if self.focus_areas:
            base += f" Core focus areas: {', '.join(self.focus_areas)}."
        if self.custom_instructions:
            base += f" {self.custom_instructions.strip()}"
        return base

    def _article_prompt(self, article: NewsArticle) -> str:
        context = f"Headline: {article.title}\nSource: {article.source}"
        if article.summary:
            context += f"\nDescription: {article.summary}"
        return (
            f"{context}\n\n"
            "Return a JSON object with these keys:\n"
            '"priority": "act" (requires CEO decision/response today) | "watch" (monitor closely) | "aware" (context only),\n'
            '"section": "competitive_intel" | "strategic_opportunity" | "regulatory_radar" | "market_signals" | "industry_pulse",\n'
            '"situation": 1-2 sentences on what happened — facts only, no spin,\n'
            '"strategic_implication": 1-2 sentences on what this means for the company\'s strategy or market position,\n'
            '"competitive_implication": 1 sentence on how this shifts the competitive landscape (or empty string if not applicable),\n'
            '"recommended_action": concrete action or consideration for the CEO (or empty string if awareness only),\n'
            '"key_people": list of up to 3 strings "Name — Title/Role",\n'
            '"tickers": list of {ticker, direction: bullish|bearish|neutral, reason} for relevant public stocks — empty list if none'
        )
