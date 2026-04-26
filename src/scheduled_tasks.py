"""
Scheduled Tasks for ML Honeypot Framework.

Runs the daily security summary email at a configurable time.

Usage:
    python src/scheduled_tasks.py

    # Or specify a custom time (24h format):
    python src/scheduled_tasks.py --time 18:00

Setup as a persistent background process:
    - Windows Task Scheduler: see EMAIL_SETUP.md
    - Linux cron: 0 8 * * * cd /path/to/project && python src/scheduled_tasks.py --once
    - Docker: add as a sidecar service in docker-compose.yml
"""

import os
import sys
import argparse
import time
import logging

# Add project root and src to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

import schedule
from alerting import EmailAlerter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("scheduler")


def run_daily_summary():
    """Execute the daily summary email."""
    logger.info("Running daily security summary...")
    alerter = EmailAlerter()

    if not alerter.is_configured():
        logger.warning("Email not configured — skipping daily summary.")
        return

    success = alerter.send_daily_summary()
    if success:
        logger.info("Daily summary sent successfully.")
    else:
        logger.error("Daily summary failed — check logs.")


def main():
    parser = argparse.ArgumentParser(description="ML Honeypot — Scheduled Tasks")
    parser.add_argument("--time", default="08:00",
                        help="Time to send daily summary (24h format, default: 08:00)")
    parser.add_argument("--once", action="store_true",
                        help="Run the summary immediately once and exit (useful for cron)")
    args = parser.parse_args()

    if args.once:
        logger.info("Running one-shot daily summary...")
        run_daily_summary()
        return

    schedule.every().day.at(args.time).do(run_daily_summary)
    logger.info("Scheduled daily summary at %s. Waiting...", args.time)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
