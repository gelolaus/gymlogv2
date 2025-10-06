from datetime import datetime, timedelta, time
from typing import Tuple

from django.db import transaction
from django.utils import timezone

from .models import GymSession, DailyGymStats


def _end_of_day(d) -> datetime:
    return datetime.combine(d, time(23, 59, 59, tzinfo=timezone.get_current_timezone()))


def close_stale_sessions_before_today() -> Tuple[int, int]:
    updated_sessions = 0
    updated_days = set()

    today = timezone.now().date()

    with transaction.atomic():
        qs = GymSession.objects.select_related("student").filter(
            is_active=True,
            check_out_time__isnull=True,
            date__lt=today,
        )
        for session in qs.iterator():
            check_in = session.check_in_time
            max_checkout_by_duration = check_in + timedelta(hours=2)
            max_checkout_by_day = _end_of_day(session.date)
            new_checkout = min(max_checkout_by_duration, max_checkout_by_day)

            duration_minutes = int((new_checkout - check_in).total_seconds() // 60)
            if duration_minutes < 0:
                duration_minutes = 0

            session.check_out_time = new_checkout
            session.duration_minutes = duration_minutes
            session.is_active = False
            session.save()

            DailyGymStats.update_daily_stats(session.student, session.date)

            updated_sessions += 1
            updated_days.add((session.student_id, session.date))

    return updated_sessions, len(updated_days)


def cap_sessions_on_previous_days_to_two_hours() -> Tuple[int, int]:
    updated_sessions = 0
    examined_sessions = 0

    today = timezone.now().date()
    max_duration = timedelta(hours=2)

    with transaction.atomic():
        qs = GymSession.objects.select_related("student").filter(
            date__lt=today,
        ).order_by("check_in_time")

        for session in qs.iterator():
            examined_sessions += 1
            if not session.check_in_time:
                continue
            if session.check_out_time:
                actual_checkout = session.check_out_time
            else:
                # If somehow still open but on previous date, treat as end of that day
                actual_checkout = _end_of_day(session.date)

            duration = actual_checkout - session.check_in_time
            if duration <= max_duration:
                continue

            capped_checkout = session.check_in_time + max_duration
            new_duration_minutes = int(max_duration.total_seconds() // 60)

            session.check_out_time = capped_checkout
            session.duration_minutes = new_duration_minutes
            session.is_active = False
            session.save()

            DailyGymStats.update_daily_stats(session.student, session.date)
            updated_sessions += 1

    return examined_sessions, updated_sessions


def run_daily_maintenance() -> None:
    close_stale_sessions_before_today()
    cap_sessions_on_previous_days_to_two_hours()


