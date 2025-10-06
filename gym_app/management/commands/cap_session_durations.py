from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from gym_app.models import GymSession, DailyGymStats


class Command(BaseCommand):
    help = "Cap all gym session durations at a maximum of 2 hours (120 minutes)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true', default=False,
            help='Show what would change without saving.'
        )
        parser.add_argument(
            '--since', type=str, default=None,
            help='Only process sessions with check_in_time on/after YYYY-MM-DD.'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        since_str = options['since']

        max_duration = timedelta(hours=2)
        updated_count = 0
        examined_count = 0

        sessions = GymSession.objects.all().order_by('check_in_time')
        if since_str:
            try:
                from datetime import datetime
                since_date = datetime.strptime(since_str, '%Y-%m-%d').date()
                sessions = sessions.filter(date__gte=since_date)
            except ValueError:
                self.stdout.write(self.style.WARNING('Invalid --since format. Use YYYY-MM-DD. Proceeding without filter.'))

        # Process in a transaction for consistency
        with transaction.atomic():
            for session in sessions.select_related('student'):
                examined_count += 1
                # Skip if missing check_in_time
                if not session.check_in_time:
                    continue

                # Determine current checkout time or now for active sessions
                if session.check_out_time:
                    actual_checkout = session.check_out_time
                else:
                    actual_checkout = timezone.now()

                # Compute duration
                duration = actual_checkout - session.check_in_time

                if duration <= max_duration:
                    # Ensure duration_minutes is accurate for completed sessions
                    if session.check_out_time and session.duration_minutes != int(duration.total_seconds() / 60):
                        if not dry_run:
                            session.duration_minutes = int(duration.total_seconds() / 60)
                            session.is_active = False
                            session.save()
                    continue

                # Overlong: cap to exactly 2 hours after check-in
                capped_checkout = session.check_in_time + max_duration
                new_duration_minutes = int(max_duration.total_seconds() / 60)

                self.stdout.write(
                    f"Capping session {session.id} ({session.student.student_id}) on {session.date} "
                    f"from {session.check_in_time} - {actual_checkout} to {capped_checkout} ({new_duration_minutes} min)"
                )

                if not dry_run:
                    session.check_out_time = capped_checkout
                    session.duration_minutes = new_duration_minutes
                    session.is_active = False
                    session.save()
                    # Update daily stats for that student/date
                    DailyGymStats.update_daily_stats(session.student, session.date)
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Examined {examined_count} sessions. Updated {updated_count} overlong sessions." + (" (dry-run)" if dry_run else "")
        ))


