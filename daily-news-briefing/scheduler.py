"""Daily scheduler: run the briefing generator at 7:00 AM PST every day."""

from __future__ import annotations

import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any

import pytz
import schedule

from config_loader import load_config
from log_setup import setup_logging

logger = logging.getLogger(__name__)


def run_briefing() -> None:
    """Import and execute the main briefing workflow."""
    try:
        from briefing_generator import BriefingGenerator
        config = load_config()
        generator = BriefingGenerator(config)
        generator.run()
    except Exception as exc:
        logger.error("Briefing run failed: %s", exc, exc_info=True)


def _next_run_info(job: schedule.Job) -> str:
    next_run = job.next_run
    if next_run is None:
        return "unknown"
    tz = pytz.timezone("America/Los_Angeles")
    return next_run.astimezone(tz).strftime("%Y-%m-%d %H:%M %Z")


def _handle_shutdown(signum: int, frame: Any) -> None:
    logger.info("Shutdown signal received — exiting gracefully")
    sys.exit(0)


def main() -> None:
    config = load_config()
    output_cfg = config.get("output", {})
    logs_folder = output_cfg.get("logs_folder", "logs")
    schedule_cfg = config.get("schedule", {})
    run_time = schedule_cfg.get("time", "07:00")

    Path(logs_folder).mkdir(parents=True, exist_ok=True)

    # setup_logging must come first — it checks for existing handlers and returns
    # early if any are found, so adding the scheduler handler afterwards is safe.
    setup_logging(logs_folder)

    import logging.handlers
    sched_log = Path(logs_folder) / "scheduler.log"
    sched_handler = logging.handlers.RotatingFileHandler(
        sched_log, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    sched_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger().addHandler(sched_handler)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    job = schedule.every().day.at(run_time).do(run_briefing)
    logger.info("Scheduler started — next run: %s", _next_run_info(job))
    print(f"Scheduler running. Daily briefing at {run_time} PST. Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
