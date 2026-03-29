"""Configure root logger: rotating file handler + console stream handler."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path


def setup_logging(logs_folder: str = "logs", level: int = logging.INFO) -> None:
    """Call once at startup to configure the root logger."""
    logs_path = Path(logs_folder)
    logs_path.mkdir(parents=True, exist_ok=True)

    log_file = logs_path / "briefing.log"

    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        return  # already configured

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file: 5 MB per file, keep 7 backups
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
