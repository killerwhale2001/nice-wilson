"""AI-powered summarizer for a Twitter/X account's recent tweets."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from models import Tweet

logger = logging.getLogger(__name__)


class XSummarizer:
    def __init__(self, config: dict[str, Any]) -> None:
        ai_cfg = config.get("ai_analysis", {})
        x_cfg = config.get("x_twitter", {}).get("summarization", {})
        self.client = OpenAI(api_key=ai_cfg.get("api_key"))
        self.model = x_cfg.get("model", ai_cfg.get("model", "gpt-4o-mini"))
        self.focus_areas: list[str] = x_cfg.get("focus_areas", [])

    def summarize(self, username: str, display_name: str, tweets: list[Tweet]) -> dict[str, Any]:
        """Return a summary dict for the given account's tweets."""
        if not tweets:
            return {
                "username": username,
                "display_name": display_name,
                "tweet_count": 0,
                "overall_summary": "",
                "key_topics": [],
                "notable_tweets": [],
                "tone_sentiment": "",
                "engagement_highlights": "",
                "top_tweets": [],
                "engagement_stats": {},
            }

        top_tweets = sorted(tweets, key=lambda t: t.engagement_score, reverse=True)[:3]
        tweet_texts = "\n".join(f"- {t.text}" for t in tweets[:30])

        prompt = self._build_prompt(username, display_name, tweet_texts)
        ai_data: dict[str, Any] = {}
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
            )
            ai_data = json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            logger.warning("X summarization failed for @%s: %s", username, exc)

        return {
            "username": username,
            "display_name": display_name,
            "tweet_count": len(tweets),
            "overall_summary": ai_data.get("overall_summary", ""),
            "key_topics": ai_data.get("key_topics", []),
            "notable_tweets": ai_data.get("notable_tweets", []),
            "tone_sentiment": ai_data.get("tone_sentiment", ""),
            "engagement_highlights": ai_data.get("engagement_highlights", ""),
            "top_tweets": [
                {
                    "text": t.text,
                    "url": t.url,
                    "likes": t.like_count,
                    "retweets": t.retweet_count,
                    "engagement": t.engagement_score,
                }
                for t in top_tweets
            ],
            "engagement_stats": self._engagement_stats(tweets),
        }

    def _system_prompt(self) -> str:
        base = "You are a social media analyst summarizing Twitter/X activity."
        if self.focus_areas:
            base += f" Focus on: {', '.join(self.focus_areas)}."
        return base

    def _build_prompt(self, username: str, display_name: str, tweet_texts: str) -> str:
        return (
            f"Summarize the recent Twitter activity of @{username} ({display_name}).\n\n"
            f"Recent tweets:\n{tweet_texts}\n\n"
            "Return a JSON object with keys:\n"
            '"overall_summary": 3-4 sentences describing their activity,\n'
            '"key_topics": list of 3-5 topic strings,\n'
            '"notable_tweets": list of 2-3 brief strings describing significant tweets,\n'
            '"tone_sentiment": single phrase describing overall tone,\n'
            '"engagement_highlights": 1 sentence on engagement patterns'
        )

    @staticmethod
    def _engagement_stats(tweets: list[Tweet]) -> dict[str, Any]:
        if not tweets:
            return {}
        return {
            "total_likes": sum(t.like_count for t in tweets),
            "total_retweets": sum(t.retweet_count for t in tweets),
            "total_replies": sum(t.reply_count for t in tweets),
            "avg_engagement": round(
                sum(t.engagement_score for t in tweets) / len(tweets), 1
            ),
        }
