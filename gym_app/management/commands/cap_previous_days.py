from django.core.management.base import BaseCommand
from django.utils import timezone

from gym_app.maintenance import cap_sessions_on_previous_days_to_two_hours


class Command(BaseCommand):
    help = "Cap sessions on previous days to 2 hours (120 minutes). Updates daily stats."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False, help='Currently ignored; operation is idempotent.')

    def handle(self, *args, **options):
        examined, updated = cap_sessions_on_previous_days_to_two_hours()
        today = timezone.now().date().isoformat()
        self.stdout.write(self.style.SUCCESS(
            f"[{today}] Examined {examined} sessions from previous days. Capped {updated} overlong sessions."
        ))


