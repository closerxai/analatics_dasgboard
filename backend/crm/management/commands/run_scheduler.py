"""
Management command: python manage.py run_scheduler

Starts the APScheduler that runs auto_sync_all() every 60 minutes.
Run this in a separate process alongside the Django server.

Usage:
    python manage.py run_scheduler

Install dependency:
    pip install apscheduler
"""

import logging
import time

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start the background scheduler for GHL auto-sync (every 60 minutes)"

    def handle(self, *args, **options):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:
            self.stderr.write(
                "APScheduler not installed. Run: pip install apscheduler"
            )
            return

        from crm.utils.ghl_sync import auto_sync_all

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            auto_sync_all,
            trigger="interval",
            minutes=60,
            id="ghl_auto_sync",
            name="GHL Auto Sync (every 60 min, pulls last 1.5h data)",
            replace_existing=True,
        )

        scheduler.start()
        self.stdout.write(
            self.style.SUCCESS("Scheduler started — GHL auto-sync runs every 60 minutes.")
        )
        self.stdout.write("Press Ctrl+C to stop.\n")

        try:
            while True:
                time.sleep(30)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            self.stdout.write(self.style.WARNING("Scheduler stopped."))
