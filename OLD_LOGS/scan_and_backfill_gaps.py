import json
import os
import sqlite3
from datetime import date, timedelta


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")
LOGS_DIR = os.path.dirname(__file__)
ALL_DATA_PATH = os.path.join(LOGS_DIR, "ALL_DATA.json")

DATE_START = date(2025, 8, 1)
DATE_END = date(2025, 8, 31)


def mmddyyyy(d: date) -> str:
    return f"{d.strftime('%m')}-{d.strftime('%d')}-{d.year}"


def sync_from_db():
    # Build existing (sid, date) keys from JSON
    with open(ALL_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    present = set()
    for r in data:
        sid = r.get("student_id")
        d = r.get("workout_date")
        if sid and d:
            present.add((sid, d))

    # Load DB aggregates across the month
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.student_id, s.first_name||' '||s.last_name as full_name,
               s.pe_course, s.block_section, gs.date,
               SUM(gs.duration_minutes) as minutes, COUNT(*) as sessions
        FROM gym_sessions gs
        JOIN gym_students s ON s.id = gs.student_id
        WHERE gs.check_out_time IS NOT NULL
          AND gs.date BETWEEN ? AND ?
        GROUP BY s.student_id, gs.date
        """,
        (DATE_START.isoformat(), DATE_END.isoformat()),
    )
    rows = cur.fetchall()
    conn.close()

    added = 0
    for sid, full_name, pe, block, iso, minutes, sessions in rows:
        out_d = f"{iso[5:7]}-{iso[8:10]}-{iso[0:4]}"
        key = (sid, out_d)
        if key in present:
            continue
        # Backfill record from DB
        hours = min((minutes or 0) / 60.0, 2.0)
        rec = {
            "workout_date": out_d,
            "full_name": full_name,
            "student_id": sid,
            "enrolled_block": (block or "").upper() or None,
            "pe_course": pe if pe in ("PEDUONE", "PEDUTWO", "PEDUTRI", "PEDUFOR") else None,
            "workout_start": None,
            "last_gym": None,
            "workout_end": None,
            "workout_time": hours,
            "completed_sessions": sessions or 0,
            "error": None,
        }
        data.append(rec)
        present.add(key)
        added += 1

    with open(ALL_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Backfilled {added} missing (student_id, date) records from DB.")


if __name__ == "__main__":
    sync_from_db()


