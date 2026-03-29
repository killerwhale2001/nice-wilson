"""Basic AI analyzer: per-article summary/impact/key-points + daily digest."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from models import NewsArticle

logger = logging.getLogger(__name__)


class AINewsAnalyzer:
    def __init__(self, config: dict[str, Any]) -> None:
        ai_cfg = config.get("ai_analysis", {})
        self.client = OpenAI(api_key=ai_cfg.get("api_key"))
        self.model = ai_cfg.get("model", "gpt-4o-mini")
        self.temperature = ai_cfg.get("temperature", 0.7)
        self.max_tokens = ai_cfg.get("max_tokens", 500)
        self.style = ai_cfg.get("analysis_style", "professional")
        self.focus_areas: list[str] = ai_cfg.get("focus_areas", [])
        self.custom_instructions: str = ai_cfg.get("custom_instructions", "")

    def analyze_article(self, article: NewsArticle) -> NewsArticle:
        """Populate ai_summary, ai_impact, ai_key_points on the article in-place."""
        prompt = self._article_prompt(article)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            article.ai_summary = data.get("summary", "")
            article.ai_impact = data.get("impact", "")
            article.ai_key_points = data.get("key_points", [])
        except Exception as exc:
            logger.warning("AI analysis failed for '%s': %s", article.title, exc)
        return article

    def generate_daily_digest(self, articles: list[NewsArticle]) -> str:
        """Generate an overall digest connecting all articles."""
        if not articles:
            return ""
        bullet_list = "\n".join(f"- {a.title} ({a.source})" for a in articles)
        prompt = (
            f"Based on these news articles from the past 24 hours:\n{bullet_list}\n\n"
            "Write a 3-4 sentence daily digest that connects the key themes and "
            "overall narrative of today's news. Be concise and insightful."
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            logger.warning("Daily digest generation failed: %s", exc)
            return ""

    # ── Prompt builders ────────────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        parts = [f"You are a {self.style} news analyst."]
        if self.focus_areas:
            parts.append(f"Focus on: {', '.join(self.focus_areas)}.")
        if self.custom_instructions:
            parts.append(self.custom_instructions.strip())
        return " ".join(parts)

    def _article_prompt(self, article: NewsArticle) -> str:
        context = f"Title: {article.title}\nSource: {article.source}"
        if article.summary:
            context += f"\nDescription: {article.summary}"
        return (
            f"{context}\n\n"
            'Return a JSON object with keys:\n'
            '"summary": 2-3 sentence digest of what happened,\n'
            '"impact": 1-2 sentences on why it matters,\n'
            '"key_points": list of 2-3 bullet strings'
        )
