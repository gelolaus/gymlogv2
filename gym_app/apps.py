from django.apps import AppConfig
from django.conf import settings
import os
import datetime


_MAINTENANCE_LAST_RUN_ENV = "GYMLOG_MAINT_LAST_RUN"


class GymAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gym_app'

    def ready(self):
        # Run once-per-process and only once per day to avoid repeated work
        try:
            from .maintenance import run_daily_maintenance
        except Exception:
            return

        today = datetime.date.today().isoformat()
        last_run = os.environ.get(_MAINTENANCE_LAST_RUN_ENV)
        if last_run == today:
            return

        # Only run in non-test environments; allow override via env
        if getattr(settings, 'RUN_STARTUP_MAINTENANCE', True):
            try:
                run_daily_maintenance()
                os.environ[_MAINTENANCE_LAST_RUN_ENV] = today
            except Exception:
                # Avoid crashing app startup due to maintenance errors
                pass
