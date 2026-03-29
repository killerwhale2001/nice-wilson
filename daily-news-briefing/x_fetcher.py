"""Fetch tweets via Nitter RSS feeds (free, no API key required)."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

import requests

from models import Tweet

logger = logging.getLogger(__name__)

_NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.1d4.us",
]
_TIMEOUT = 15
_RETRY_DELAY = 3


class XFetcher:
    def __init__(self, config: dict[str, Any]) -> None:
        x_cfg = config.get("x_twitter", {})
        custom_instance = x_cfg.get("nitter_instance")
        self.instances = [custom_instance] + _NITTER_INSTANCES if custom_instance else _NITTER_INSTANCES
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (compatible; NewsBriefingBot/1.0)"
        )

    def fetch_user_tweets(
        self,
        username: str,
        max_tweets: int = 50,
        exclude_replies: bool = False,
        exclude_retweets: bool = False,
    ) -> list[Tweet]:
        """Return tweets from the past 24 hours for the given username."""
        rss_text = self._fetch_rss(username)
        if not rss_text:
            return []
        tweets = self._parse_rss(rss_text, username)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        tweets = [t for t in tweets if t.created_at >= cutoff]
        if exclude_replies:
            tweets = [t for t in tweets if not t.text.startswith("@")]
        if exclude_retweets:
            tweets = [t for t in tweets if not t.text.startswith("RT @")]
        return tweets[:max_tweets]

    # ── RSS fetching ───────────────────────────────────────────────────────────

    def _fetch_rss(self, username: str) -> str | None:
        for instance in self.instances:
            url = f"{instance}/{username}/rss"
            try:
                resp = self._session.get(url, timeout=_TIMEOUT)
                if resp.status_code == 200:
                    logger.debug("Fetched RSS for @%s from %s", username, instance)
                    return resp.text
                logger.debug("Instance %s returned %d for @%s", instance, resp.status_code, username)
            except requests.RequestException as exc:
                logger.debug("Instance %s failed for @%s: %s", instance, username, exc)
            time.sleep(_RETRY_DELAY)  # only reached on failure — success returns above
        logger.warning("All Nitter instances failed for @%s — skipping", username)
        return None

    # ── RSS parsing ────────────────────────────────────────────────────────────

    def _parse_rss(self, rss_text: str, username: str) -> list[Tweet]:
        tweets: list[Tweet] = []
        try:
            root = ElementTree.fromstring(rss_text)
        except ElementTree.ParseError as exc:
            logger.warning("RSS parse error for @%s: %s", username, exc)
            return []

        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        channel = root.find("channel")
        if channel is None:
            return []

        # Author name from channel title (format: "username / Display Name")
        channel_title = (channel.findtext("title") or "").split(" / ")
        display_name = channel_title[1].strip() if len(channel_title) > 1 else username

        for item in channel.findall("item"):
            link = item.findtext("link") or ""
            tweet_id = self._extract_id(link)
            text = self._clean_text(item.findtext("title") or "")
            pub_date_str = item.findtext("pubDate") or ""
            created_at = self._parse_date(pub_date_str)
            twitter_url = self._nitter_to_twitter(link)

            tweets.append(
                Tweet(
                    id=tweet_id,
                    text=text,
                    created_at=created_at,
                    author_username=username,
                    author_name=display_name,
                    url=twitter_url,
                )
            )
        return tweets

    @staticmethod
    def _extract_id(url: str) -> str:
        match = re.search(r"/status/(\d+)", url)
        return match.group(1) if match else url

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        try:
            return parsedate_to_datetime(date_str).astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def _nitter_to_twitter(url: str) -> str:
        """Convert a Nitter URL to its twitter.com equivalent."""
        return re.sub(r"https?://[^/]+/", "https://twitter.com/", url, count=1)
