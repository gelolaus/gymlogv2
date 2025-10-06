import json
import os
import sqlite3
import sys
from datetime import date
import re
import unicodedata


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")
LOGS_DIR = os.path.dirname(__file__)
ALL_DATA_PATH = os.path.join(LOGS_DIR, "ALL_DATA.json")


def strip_accents(text: str) -> str:
    if not text:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )


def normalize(s: str) -> str:
    n = strip_accents((s or "").strip().lower().replace('.', ' '))
    n = re.sub(r"\s+", " ", n)
    tokens = [t for t in n.split(' ') if len(t) > 1]
    return ' '.join(tokens)


def load_json_by_name(name_key: str, start_iso: str, end_iso: str):
    with open(ALL_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Map YYYY-MM-DD -> total_hours, sessions
    aggregate = {}
    for r in data:
        if normalize(r.get("full_name")) != name_key:
            continue
        wd = r.get("workout_date")  # MM-DD-YYYY
        if not wd:
            continue
        mm, dd, yyyy = wd.split("-")
        iso = f"{yyyy}-{mm}-{dd}"
        if not (start_iso <= iso <= end_iso):
            continue
        hours = float(r.get("workout_time") or 0.0)
        sess = int(r.get("completed_sessions") or 0)
        if iso not in aggregate:
            aggregate[iso] = {"hours": 0.0, "sessions": 0}
        aggregate[iso]["hours"] += hours
        aggregate[iso]["sessions"] += sess
    return aggregate


def load_db_by_name(last_like: str, first_like: str, start_iso: str, end_iso: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT gs.date, SUM(gs.duration_minutes) AS minutes, COUNT(*) AS sessions
        FROM gym_sessions gs
        JOIN gym_students s ON s.id = gs.student_id
        WHERE lower(s.last_name) LIKE lower(?)
          AND lower(s.first_name) LIKE lower(?)
          AND gs.check_out_time IS NOT NULL
          AND gs.date BETWEEN ? AND ?
        GROUP BY gs.date
        ORDER BY gs.date
        """,
        (last_like, first_like, start_iso, end_iso),
    )
    rows = cur.fetchall()
    conn.close()
    return {d: {"hours": (m or 0)/60.0, "sessions": s or 0} for d, m, s in rows}


def main():
    if len(sys.argv) < 3:
        print("Usage: python OLD_LOGS/verify_student_days.py <first_name> <last_name> [YYYY-MM]")
        return
    first = sys.argv[1]
    last = sys.argv[2]
    ym = sys.argv[3] if len(sys.argv) >= 4 else "2025-08"
    start_iso = f"{ym}-01"
    end_iso = f"{ym}-31"

    name_key = normalize(f"{first} {last}")
    json_agg = load_json_by_name(name_key, start_iso, end_iso)
    db_agg = load_db_by_name(last + '%', first + '%', start_iso, end_iso)

    all_days = sorted(set(json_agg.keys()) | set(db_agg.keys()))
    print("date, db_hours, json_hours, db_sessions, json_sessions")
    for d in all_days:
        dbh = db_agg.get(d, {}).get("hours", 0.0)
        jh = json_agg.get(d, {}).get("hours", 0.0)
        dbs = db_agg.get(d, {}).get("sessions", 0)
        js = json_agg.get(d, {}).get("sessions", 0)
        print(f"{d},{dbh:.4f},{jh:.4f},{dbs},{js}")


if __name__ == "__main__":
    main()


