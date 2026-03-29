"""Main orchestrator: run the full CEO executive briefing pipeline."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ai_news_analyzer import AINewsAnalyzer
from ai_news_analyzer_enhanced import AINewsAnalyzerEnhanced
from config_loader import load_config
from content_filter import ContentFilter
from email_delivery import EmailDelivery
from log_setup import setup_logging
from models import NewsArticle
from news_api_fetcher import NewsAPIFetcher
from news_fetcher import NewsFetcher
from news_ranker import NewsRanker
from news_summarizer import NewsSummarizer
from x_fetcher import XFetcher
from x_summarizer import XSummarizer

logger = logging.getLogger(__name__)

_PRIORITY_ICON = {"act": "🔴", "watch": "🟡", "aware": "🟢"}
_PRIORITY_LABEL = {"act": "REQUIRES ACTION", "watch": "MONITOR", "aware": "AWARE"}
_DIRECTION_ICON = {"bullish": "▲", "bearish": "▼", "neutral": "—"}

_SECTIONS = [
    ("competitive_intel",      "⚔️  COMPETITIVE INTELLIGENCE"),
    ("strategic_opportunity",  "🎯  STRATEGIC OPPORTUNITY"),
    ("regulatory_radar",       "⚖️  REGULATORY RADAR"),
    ("market_signals",         "📊  MARKET SIGNALS"),
    ("industry_pulse",         "📡  INDUSTRY PULSE"),
]


class BriefingGenerator:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.continue_on_error: bool = config.get("error_handling", {}).get("continue_on_error", True)
        output_cfg = config.get("output", {})
        self.reports_folder = Path(output_cfg.get("reports_folder", "reports"))
        self.filename_pattern: str = output_cfg.get("filename_pattern", "news_briefing_{date}.md")
        self.reports_folder.mkdir(parents=True, exist_ok=True)

    def run(self) -> str | None:
        logger.info("=== Starting executive briefing generation ===")

        # ── Fetch ──────────────────────────────────────────────────────────────
        articles: list[NewsArticle] = self._step("Fetch NewsAPI", self._fetch_newsapi, default=[])
        articles += self._step("Fetch scraped", self._fetch_scraped, default=[])
        articles = self._deduplicate(articles)
        articles = self._filter_24h(articles)
        logger.info("Fetched %d unique articles within 36 hours", len(articles))

        # ── Filter & rank ──────────────────────────────────────────────────────
        articles, filter_stats = self._step("Content filter", lambda: ContentFilter(self.config).filter(articles), default=(articles, None))
        if filter_stats:
            logger.info("Content filter: %d passed, %d excluded", filter_stats.passed, filter_stats.filtered)
        articles = self._step("Rank", lambda: NewsRanker(self.config).rank(articles), default=articles)

        if not articles:
            logger.warning("No articles after filtering/ranking — aborting")
            return None

        # ── Analyze ────────────────────────────────────────────────────────────
        self._step("Fallback summaries", lambda: self._summarize_fallback(articles), default=None)
        analyzer = self._build_analyzer()
        articles = self._step("AI analysis", lambda: self._analyze_articles(analyzer, articles), default=articles)

        board_summary = ""
        tldr: list[str] = []
        market_watch: list[dict[str, Any]] = []
        what_to_watch: list[str] = []

        if isinstance(analyzer, AINewsAnalyzerEnhanced):
            board_summary = self._step("Board summary", lambda: analyzer.generate_board_summary(articles), default="")
            tldr = self._step("TL;DR", lambda: analyzer.generate_tldr(articles), default=[])
            market_watch = self._step("Market watch", lambda: analyzer.generate_market_watch(articles), default=[])
            what_to_watch = self._step("What to watch", lambda: analyzer.generate_what_to_watch(articles), default=[])

        # ── Twitter ────────────────────────────────────────────────────────────
        twitter_summaries = self._step("Twitter/X", self._fetch_twitter, default=[])

        # ── Render, save, send ─────────────────────────────────────────────────
        report_md = self._render_report(articles, board_summary, tldr, market_watch, what_to_watch, twitter_summaries)
        report_path = self._save_report(report_md)
        logger.info("Report saved: %s", report_path)
        self._step("Send email", lambda: EmailDelivery(self.config).send(report_md, str(report_path)), default=False)

        logger.info("=== Briefing complete ===")
        return str(report_path)

    # ── Pipeline stages ────────────────────────────────────────────────────────

    def _fetch_newsapi(self) -> list[NewsArticle]:
        newsapi_cfg = self.config.get("newsapi", {})
        if not newsapi_cfg.get("enabled", True):
            return []
        api_key = newsapi_cfg.get("api_key", "")
        if not api_key:
            logger.warning("NEWS_API_KEY not set — skipping NewsAPI")
            return []
        err = self.config.get("error_handling", {})
        fetcher = NewsAPIFetcher(api_key, retry_attempts=err.get("retry_attempts", 3), retry_delay=err.get("retry_delay", 5))
        articles: list[NewsArticle] = []
        for cat in newsapi_cfg.get("categories", []):
            if cat.get("enabled", True):
                articles += fetcher.fetch_by_category(cat["category"], cat.get("max_articles", 5))
        for kw in newsapi_cfg.get("keywords", []):
            if kw.get("enabled", True):
                articles += fetcher.fetch_by_keywords(kw["query"], kw.get("category", "General"), kw.get("max_articles", 5))
        for src in newsapi_cfg.get("sources", []):
            if src.get("enabled", True):
                articles += fetcher.fetch_by_source(src["source_id"], src.get("category", "General"), src.get("max_articles", 5))
        logger.info("NewsAPI: %d articles", len(articles))
        return articles

    def _fetch_scraped(self) -> list[NewsArticle]:
        fetcher = NewsFetcher()
        articles: list[NewsArticle] = []
        for source in self.config.get("news_sources", []):
            if source.get("enabled", True):
                articles += fetcher.fetch(source["url"], source.get("category", "General"), source.get("name", source["url"]), source.get("max_articles", 5))
        logger.info("Scraped: %d articles", len(articles))
        return articles

    def _summarize_fallback(self, articles: list[NewsArticle]) -> None:
        s = NewsSummarizer()
        for a in articles:
            s.summarize(a)

    def _build_analyzer(self) -> AINewsAnalyzerEnhanced | AINewsAnalyzer:
        ai_cfg = self.config.get("ai_analysis", {})
        if ai_cfg.get("enabled", True) and ai_cfg.get("use_enhanced", True):
            return AINewsAnalyzerEnhanced(self.config)
        return AINewsAnalyzer(self.config)

    def _analyze_articles(self, analyzer: Any, articles: list[NewsArticle]) -> list[NewsArticle]:
        for i, a in enumerate(articles, 1):
            logger.debug("Analyzing %d/%d: %s", i, len(articles), a.title)
            analyzer.analyze_article(a)
        return articles

    def _fetch_twitter(self) -> list[dict[str, Any]]:
        x_cfg = self.config.get("x_twitter", {})
        if not x_cfg.get("enabled", True):
            return []
        fetcher = XFetcher(self.config)
        summarizer = XSummarizer(self.config)
        results = []
        for acct in x_cfg.get("accounts", []):
            if acct.get("enabled", True):
                tweets = fetcher.fetch_user_tweets(acct["username"], max_tweets=acct.get("max_tweets", 20), exclude_replies=acct.get("exclude_replies", False), exclude_retweets=acct.get("exclude_retweets", False))
                results.append(summarizer.summarize(acct["username"], acct.get("display_name", acct["username"]), tweets))
        return results

    # ── Report rendering ───────────────────────────────────────────────────────

    def _render_report(
        self,
        articles: list[NewsArticle],
        board_summary: str,
        tldr: list[str],
        market_watch: list[dict[str, Any]],
        what_to_watch: list[str],
        twitter_summaries: list[dict[str, Any]],
    ) -> str:
        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.strftime("%B %d, %Y")
        time_str = now_utc.strftime("%H:%M UTC")

        L: list[str] = []

        # ── Header ─────────────────────────────────────────────────────────────
        L += [
            "# EXECUTIVE BRIEFING",
            f"### {date_str} &nbsp;|&nbsp; {time_str} &nbsp;|&nbsp; CONFIDENTIAL",
            "",
            "---",
            "",
        ]

        # ── Board Summary ──────────────────────────────────────────────────────
        if board_summary:
            L += [
                "## BOARD SUMMARY",
                "",
                f"> {board_summary}",
                "",
                "---",
                "",
            ]

        # ── TL;DR ─────────────────────────────────────────────────────────────
        if tldr:
            L += ["## ⚡ TODAY IN 30 SECONDS", ""]
            for bullet in tldr:
                L.append(f"- {bullet}")
            L += ["", "---", ""]

        # ── Immediate Attention ────────────────────────────────────────────────
        action_items = [a for a in articles if a.priority == "act"]
        if action_items:
            L += ["## 🔴 IMMEDIATE ATTENTION REQUIRED", ""]
            for a in action_items:
                L += self._render_article(a)
            L += ["---", ""]

        # ── Sections ──────────────────────────────────────────────────────────
        for section_key, section_title in _SECTIONS:
            # exclude act items already shown above
            section_articles = [a for a in articles if a.report_section == section_key and a.priority != "act"]
            if not section_articles:
                continue
            L += [f"## {section_title}", ""]
            for a in sorted(section_articles, key=lambda x: {"watch": 0, "aware": 1}.get(x.priority, 1)):
                L += self._render_article(a)
            L += ["---", ""]

        # ── Market Watch ──────────────────────────────────────────────────────
        if market_watch:
            L += ["## 📈 MARKET WATCH", ""]
            L.append("| Ticker | Signal | Context |")
            L.append("|--------|--------|---------|")
            for entry in market_watch:
                icon = _DIRECTION_ICON.get(entry.get("direction", "neutral"), "—")
                direction = entry.get("direction", "neutral").upper()
                reasons = "; ".join(entry.get("reasons", []))[:120]
                L.append(f"| **{entry['ticker']}** | {icon} {direction} | {reasons} |")
            L += ["", "---", ""]

        # ── What to Watch ──────────────────────────────────────────────────────
        if what_to_watch:
            L += ["## 👀 WHAT TO WATCH", ""]
            for item in what_to_watch:
                L.append(f"- {item}")
            L += ["", "---", ""]

        # ── Voices That Matter ─────────────────────────────────────────────────
        active_voices = [tw for tw in twitter_summaries if tw.get("tweet_count", 0) > 0]
        if active_voices:
            L += ["## 🎙️ VOICES THAT MATTER", ""]
            L.append("*Key industry figures active in the last 24 hours — intelligence only.*")
            L.append("")
            for tw in active_voices:
                L += [f"**{tw['display_name']}** (@{tw['username']})"]
                if tw.get("overall_summary"):
                    L.append(tw["overall_summary"])
                if tw.get("key_topics"):
                    L.append(f"*Topics: {', '.join(tw['key_topics'])}*")
                if tw.get("notable_tweets"):
                    for note in tw["notable_tweets"]:
                        L.append(f"> {note}")
                L.append("")
            L += ["---", ""]

        # ── Footer ────────────────────────────────────────────────────────────
        L += [
            f"*Briefing generated {date_str} at {time_str} &nbsp;|&nbsp; "
            f"{len(articles)} sources reviewed &nbsp;|&nbsp; CONFIDENTIAL*",
        ]

        return "\n".join(L)

    def _render_article(self, article: NewsArticle) -> list[str]:
        """Render a single article in executive briefing style."""
        priority_icon = _PRIORITY_ICON.get(article.priority, "🟢")
        priority_label = _PRIORITY_LABEL.get(article.priority, "AWARE")

        L: list[str] = [
            f"### {priority_icon} {article.title}",
            "",
            f"*{article.source} &nbsp;|&nbsp; {priority_label}*",
            "",
        ]

        if article.situation:
            L += [f"**Situation:** {article.situation}", ""]

        if article.strategic_implication:
            L += [f"**Strategic Implication:** {article.strategic_implication}", ""]

        if article.competitive_implication:
            L += [f"**Competitive Impact:** {article.competitive_implication}", ""]

        if article.recommended_action:
            L += [f"**→ Recommended Action:** {article.recommended_action}", ""]

        # Tickers and key people on one line each
        meta: list[str] = []
        if article.tickers:
            parts = [f"{_DIRECTION_ICON.get(t.get('direction','neutral'),'—')} {t.get('ticker','')}" for t in article.tickers if t.get('ticker')]
            meta.append(f"**Tickers:** {' &nbsp; '.join(parts)}")
        if article.key_people:
            meta.append(f"**Key People:** {' · '.join(article.key_people)}")
        L += meta

        L += ["", f"[Read full briefing source →]({article.url})", ""]
        return L

    def _save_report(self, content: str) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = self.reports_folder / self.filename_pattern.replace("{date}", date_str)
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def _deduplicate(articles: list[NewsArticle]) -> list[NewsArticle]:
        seen: set[str] = set()
        unique: list[NewsArticle] = []
        for a in articles:
            if a.url not in seen and a.title not in seen:
                seen.add(a.url)
                seen.add(a.title)
                unique.append(a)
        return unique

    @staticmethod
    def _filter_24h(articles: list[NewsArticle]) -> list[NewsArticle]:
        """Safety-net: drop anything published more than 36 hours ago."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
        kept, dropped = [], 0
        for a in articles:
            try:
                dt = datetime.fromisoformat(a.published_date.replace("Z", "+00:00"))
                if dt >= cutoff:
                    kept.append(a)
                else:
                    dropped += 1
            except (ValueError, TypeError, AttributeError):
                kept.append(a)  # keep if date missing or unparseable (e.g. scraped articles)
        if dropped:
            logger.info("36h filter: dropped %d articles older than 36 hours", dropped)
        return kept

    def _step(self, name: str, fn: Any, *, default: Any) -> Any:
        try:
            return fn()
        except Exception as exc:
            logger.error("Step '%s' failed: %s", name, exc, exc_info=True)
            if not self.continue_on_error:
                raise
            return default


def main() -> None:
    config = load_config()
    setup_logging(config.get("output", {}).get("logs_folder", "logs"))
    BriefingGenerator(config).run()


if __name__ == "__main__":
    main()
