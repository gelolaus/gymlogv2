import os
import sqlite3
from datetime import datetime, timedelta, time, date as date_cls
import argparse


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")


def parse_iso_date(date_str: str) -> date_cls:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def end_of_day(d: date_cls) -> datetime:
    return datetime.combine(d, time(23, 59, 59))


def close_open_sessions(cutoff_date: date_cls) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Find all active sessions with no checkout on or before cutoff
    cur.execute(
        """
        SELECT id, student_id, check_in_time, date
        FROM gym_sessions
        WHERE check_out_time IS NULL
          AND is_active = 1
          AND date <= ?
        ORDER BY date ASC, id ASC
        """,
        (cutoff_date.isoformat(),),
    )
    rows = cur.fetchall()

    affected_pairs = set()  # (student_id, date)
    updated = 0

    for session_id, student_id, check_in_str, session_date_str in rows:
        # Parse fields
        try:
            check_in_dt = datetime.fromisoformat(check_in_str)
        except ValueError:
            # Fallback: allow "YYYY-MM-DD HH:MM:SS" without microseconds TZ
            check_in_dt = datetime.strptime(check_in_str, "%Y-%m-%d %H:%M:%S")

        session_date = datetime.fromisoformat(session_date_str).date() if "T" in session_date_str else datetime.strptime(session_date_str, "%Y-%m-%d").date()

        # Compute checkout capped to 120 minutes and end-of-day
        max_checkout_by_duration = check_in_dt + timedelta(minutes=120)
        max_checkout_by_day = end_of_day(session_date)
        new_checkout = min(max_checkout_by_duration, max_checkout_by_day)

        # Ensure non-negative duration
        duration_seconds = max(0, int((new_checkout - check_in_dt).total_seconds()))
        new_duration_minutes = duration_seconds // 60

        # Update the session
        cur.execute(
            """
            UPDATE gym_sessions
            SET check_out_time = ?, duration_minutes = ?, is_active = 0
            WHERE id = ?
            """,
            (new_checkout.isoformat(sep=' '), int(new_duration_minutes), session_id),
        )

        affected_pairs.add((student_id, session_date.isoformat()))
        updated += 1

    # Recompute daily stats for affected student/day pairs
    for student_id, iso_date in affected_pairs:
        # Aggregate from sessions table
        cur.execute(
            """
            SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes,
                   COUNT(*) AS total_sessions
            FROM gym_sessions
            WHERE student_id = ? AND date = ? AND check_out_time IS NOT NULL
            """,
            (student_id, iso_date),
        )
        total_minutes, total_sessions = cur.fetchone()

        # Upsert into gym_daily_stats
        cur.execute(
            "SELECT id FROM gym_daily_stats WHERE student_id = ? AND date = ?",
            (student_id, iso_date),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE gym_daily_stats SET total_minutes = ?, total_sessions = ? WHERE id = ?",
                (int(total_minutes or 0), int(total_sessions or 0), row[0]),
            )
        else:
            cur.execute(
                "INSERT INTO gym_daily_stats (student_id, date, total_sessions, total_minutes) VALUES (?, ?, ?, ?)",
                (student_id, iso_date, int(total_sessions or 0), int(total_minutes or 0)),
            )

    conn.commit()
    conn.close()

    return {
        "open_sessions_found": len(rows),
        "sessions_closed": updated,
        "days_updated": len(affected_pairs),
    }


def main():
    parser = argparse.ArgumentParser(description="Close lingering active sessions on or before a cutoff date.")
    parser.add_argument(
        "--cutoff",
        dest="cutoff",
        default="2025-10-05",
        help="Cutoff date in YYYY-MM-DD (inclusive). Default: 2025-10-05",
    )
    args = parser.parse_args()

    cutoff = parse_iso_date(args.cutoff)
    result = close_open_sessions(cutoff)

    print("Closed lingering sessions up to:", cutoff.isoformat())
    print(f"- Open sessions found: {result['open_sessions_found']}")
    print(f"- Sessions closed: {result['sessions_closed']}")
    print(f"- Affected student-days updated: {result['days_updated']}")


if __name__ == "__main__":
    main()


