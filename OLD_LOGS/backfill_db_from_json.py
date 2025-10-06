import json
import os
import sqlite3
from datetime import datetime, timedelta


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")
LOGS_DIR = os.path.dirname(__file__)
ALL_DATA_PATH = os.path.join(LOGS_DIR, "ALL_DATA.json")


def to_iso_date(mmddyyyy: str) -> str:
    mm, dd, yyyy = mmddyyyy.split("-")
    return f"{yyyy}-{mm}-{dd}"


def ensure_minutes_for_day(cur, student_pk: int, iso_date: str, target_minutes: int):
    # Sum existing completed minutes for that day
    cur.execute(
        "SELECT COALESCE(SUM(duration_minutes),0) FROM gym_sessions WHERE student_id=? AND date=? AND check_out_time IS NOT NULL",
        (student_pk, iso_date),
    )
    present_minutes = int(cur.fetchone()[0] or 0)
    if present_minutes >= target_minutes:
        return 0

    add_minutes = target_minutes - present_minutes
    # Create one synthetic session at midday
    check_in = datetime.fromisoformat(iso_date + "T12:00:00")
    check_out = check_in + timedelta(minutes=add_minutes)
    cur.execute(
        """
        INSERT INTO gym_sessions (student_id, check_in_time, check_out_time, duration_minutes, date, is_active)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (student_pk, check_in.isoformat(sep=' '), check_out.isoformat(sep=' '), add_minutes, iso_date),
    )

    # Update or create daily stats
    cur.execute(
        "SELECT id, total_sessions, total_minutes FROM gym_daily_stats WHERE student_id=? AND date=?",
        (student_pk, iso_date),
    )
    row = cur.fetchone()
    if row:
        stat_id, sess, mins = row
        cur.execute(
            "UPDATE gym_daily_stats SET total_sessions=?, total_minutes=? WHERE id=?",
            (int(sess or 0) + 1, int(mins or 0) + add_minutes, stat_id),
        )
    else:
        cur.execute(
            "INSERT INTO gym_daily_stats (student_id, date, total_sessions, total_minutes) VALUES (?, ?, ?, ?)",
            (student_pk, iso_date, 1, add_minutes),
        )

    return add_minutes


def main():
    with open(ALL_DATA_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Build desired per (student_id, date)
    desired = {}
    for r in records:
        sid = r.get("student_id")
        wd = r.get("workout_date")
        wt = r.get("workout_time")
        if not sid or not wd or wt is None:
            continue
        # hours to minutes, cap 120
        minutes = int(round(float(wt) * 60))
        minutes = min(minutes, 120)
        iso = to_iso_date(wd)
        key = (sid, iso)
        # Keep the max target for the day
        desired[key] = max(desired.get(key, 0), minutes)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys=ON")

    # Map student_id string to primary key id
    cur.execute("SELECT id, student_id FROM gym_students")
    sid_to_pk = {sid: pk for pk, sid in cur.fetchall()}

    total_added_minutes = 0
    total_days_touched = 0
    for (sid, iso), minutes in desired.items():
        student_pk = sid_to_pk.get(sid)
        if not student_pk:
            continue  # student not in DB; skip
        added = ensure_minutes_for_day(cur, student_pk, iso, minutes)
        if added > 0:
            total_added_minutes += added
            total_days_touched += 1

    conn.commit()
    conn.close()
    print(f"Backfill completed. Added {total_added_minutes} minutes across {total_days_touched} student-days.")


if __name__ == "__main__":
    main()


