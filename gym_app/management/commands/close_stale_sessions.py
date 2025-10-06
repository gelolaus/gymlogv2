from django.core.management.base import BaseCommand
from django.utils import timezone

from gym_app.maintenance import close_stale_sessions_before_today


class Command(BaseCommand):
    help = "Close any active sessions from previous days (before today), capping to 2 hours or end-of-day, and update daily stats."

    def handle(self, *args, **options):
        updated_sessions, updated_days = close_stale_sessions_before_today()
        today = timezone.now().date().isoformat()
        self.stdout.write(self.style.SUCCESS(
            f"[{today}] Closed {updated_sessions} stale sessions across {updated_days} student-days."
        ))


