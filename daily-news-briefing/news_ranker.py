"""AI-powered news importance ranker (0-100 scale)."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from models import NewsArticle

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10  # articles per GPT call to reduce API usage


class NewsRanker:
    def __init__(self, config: dict[str, Any]) -> None:
        rank_cfg = config.get("news_ranking", {})
        ai_cfg = config.get("ai_analysis", {})
        self.enabled: bool = rank_cfg.get("enabled", True)
        self.top_n: int = rank_cfg.get("top_n", 10)
        self.min_score: float = rank_cfg.get("min_score", 60)
        self.model: str = rank_cfg.get("model", ai_cfg.get("model", "gpt-4o-mini"))
        self.criteria: list[str] = rank_cfg.get(
            "ranking_criteria",
            ["global impact", "business significance", "technological innovation", "market relevance", "urgency"],
        )
        self.user_interests: list[str] = rank_cfg.get("user_interests", [])
        self.client = OpenAI(api_key=ai_cfg.get("api_key"))

    def rank(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Score, classify, sort, and filter articles. Returns top_n above min_score."""
        if not self.enabled or not articles:
            return articles

        # Score in batches to limit token usage
        for i in range(0, len(articles), _BATCH_SIZE):
            batch = articles[i : i + _BATCH_SIZE]
            self._score_batch(batch)

        articles.sort(key=lambda a: a.importance_score, reverse=True)
        filtered = [a for a in articles if a.importance_score >= self.min_score]
        result = filtered[: self.top_n]

        logger.info(
            "Ranker: %d articles scored, %d above min_score %d, returning top %d",
            len(articles), len(filtered), self.min_score, len(result),
        )
        return result

    def ranking_stats(self, articles: list[NewsArticle]) -> dict[str, Any]:
        scored = [a for a in articles if a.importance_score > 0]
        high = sum(1 for a in scored if a.importance_score >= 75)
        medium = sum(1 for a in scored if 50 <= a.importance_score < 75)
        low = sum(1 for a in scored if a.importance_score < 50)
        return {
            "total_scored": len(scored),
            "high": high,
            "medium": medium,
            "low": low,
            "avg_score": round(sum(a.importance_score for a in scored) / len(scored), 1) if scored else 0,
        }

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _score_batch(self, articles: list[NewsArticle]) -> None:
        numbered = "\n".join(
            f"{i+1}. {a.title} [{a.source}]" for i, a in enumerate(articles)
        )
        criteria_str = ", ".join(self.criteria)
        interests_str = f" Prioritize topics related to: {', '.join(self.user_interests)}." if self.user_interests else ""
        prompt = (
            f"Score each article 0-100 based on: {criteria_str}.{interests_str}\n\n"
            f"{numbered}\n\n"
            "Return a JSON object where keys are the article numbers (as strings) "
            'and values are integer scores. Example: {"1": 85, "2": 42}'
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a news importance scoring system. Return only the requested JSON."},
                    {"role": "user", "content": prompt},
                ],
            )
            scores: dict[str, Any] = json.loads(resp.choices[0].message.content or "{}")
            for i, article in enumerate(articles):
                score = float(scores.get(str(i + 1), 0))
                article.importance_score = score
                article.importance_label = self._label(score)
        except Exception as exc:
            logger.warning("Ranking batch failed: %s", exc)

    @staticmethod
    def _label(score: float) -> str:
        if score >= 75:
            return "HIGH"
        if score >= 50:
            return "MEDIUM"
        return "LOW"
