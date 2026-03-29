"""Load and validate configuration from config.yaml, with env var overrides for secrets."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_ENV_OVERRIDES = {
    "OPENAI_API_KEY": ("ai_analysis", "api_key"),
    "NEWS_API_KEY": ("newsapi", "api_key"),
    "EMAIL_ADDRESS": ("email_delivery", "sender_email"),
    "EMAIL_PASSWORD": ("email_delivery", "sender_password"),
}


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Load config.yaml and inject secrets from environment variables."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open() as f:
        config: dict[str, Any] = yaml.safe_load(f) or {}

    for env_var, (section, key) in _ENV_OVERRIDES.items():
        value = os.environ.get(env_var)
        if value:
            config.setdefault(section, {})[key] = value
            logger.debug("Loaded %s from environment", env_var)

    return config
