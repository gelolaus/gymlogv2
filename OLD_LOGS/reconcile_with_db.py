import json
import os
import re
import sqlite3
from collections import defaultdict
import unicodedata
from datetime import date, timedelta


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")
LOGS_DIR = os.path.dirname(__file__)
ALL_DATA_PATH = os.path.join(LOGS_DIR, "ALL_DATA.json")

DATE_START = date(2025, 8, 1)
DATE_END = date(2025, 8, 31)


def strip_accents(text: str) -> str:
    if not text:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )


def normalize_name(name: str) -> str:
    if not name:
        return ""
    # Lowercase, remove accents and periods, collapse spaces
    n = strip_accents(name).lower().replace('.', ' ')
    n = re.sub(r"\s+", " ", n).strip()
    # Drop middle single-letter tokens (e.g., "s" in "gian ace s buaquina")
    tokens = [t for t in n.split(' ') if len(t) > 1]
    return ' '.join(tokens)


def preferred_student_id(ids):
    # Prefer IDs like 202x-140xxx or 202x-040xxx, then any valid 20xx-xxxxxx
    if not ids:
        return None
    ids = list({i for i in ids if i})
    if not ids:
        return None
    pattern_priority = [
        re.compile(r"^202\d-(140|040)\d{3}$"),
        re.compile(r"^20\d{2}-\d{6}$"),
    ]
    for pat in pattern_priority:
        for sid in ids:
            if pat.fullmatch(sid):
                return sid
    return ids[0]


def load_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Load students
    cur.execute(
        """
        SELECT id, student_id, first_name, last_name, pe_course, block_section
        FROM gym_students
        """
    )
    students = cur.fetchall()

    student_by_pk = {}
    student_by_sid = {}
    student_by_name = defaultdict(list)

    for row in students:
        pk = row["id"]
        sid = row["student_id"]
        full_name = f"{row['first_name']} {row['last_name']}".strip()
        info = {
            "pk": pk,
            "student_id": sid,
            "full_name": full_name,
            "name_key": normalize_name(full_name),
            "pe_course": row["pe_course"],
            "block_section": (row["block_section"] or "").upper(),
        }
        student_by_pk[pk] = info
        student_by_sid[sid] = info
        student_by_name[info["name_key"]].append(info)

    # Load session aggregates by student_id and date
    cur.execute(
        """
        SELECT s.student_id as student_id,
               gs.date as session_date,
               SUM(gs.duration_minutes) as total_minutes,
               COUNT(*) as total_sessions
        FROM gym_sessions gs
        JOIN gym_students s ON s.id = gs.student_id
        WHERE gs.check_out_time IS NOT NULL
          AND gs.date BETWEEN ? AND ?
        GROUP BY s.student_id, gs.date
        """,
        (DATE_START.isoformat(), DATE_END.isoformat()),
    )
    session_rows = cur.fetchall()

    sessions_by_sid_date = {}
    for r in session_rows:
        sid = r["student_id"]
        d = r["session_date"]
        sessions_by_sid_date[(sid, d)] = {
            "minutes": int(r["total_minutes"]) if r["total_minutes"] is not None else 0,
            "sessions": int(r["total_sessions"]) if r["total_sessions"] is not None else 0,
        }

    conn.close()
    return student_by_sid, student_by_name, sessions_by_sid_date


def mmddyyyy(d: date) -> str:
    return f"{d.strftime('%m')}-{d.strftime('%d')}-{d.year}"


def validate_student_id(sid: str) -> bool:
    return bool(sid) and re.fullmatch(r"20\d{2}-\d{6}", sid) is not None


def map_pe(pe: str) -> str:
    if not pe:
        return None
    pe = pe.strip().upper()
    if pe in {"PEDUONE", "PEDUTWO", "PEDUTRI", "PEDUFOR"}:
        return pe
    return None


def cap_hours(hours: float) -> float:
    if hours is None:
        return None
    return min(hours, 2.0)


def main():
    # Load DB
    student_by_sid, student_by_name, sessions_by_sid_date = load_db()

    # Load ALL_DATA
    with open(ALL_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # First pass: unify student IDs by name preference
    name_to_ids = defaultdict(set)
    for rec in data:
        name_to_ids[normalize_name(rec.get("full_name"))].add(rec.get("student_id"))

    name_to_preferred = {
        name: preferred_student_id(ids) for name, ids in name_to_ids.items()
    }

    # Second pass: reconcile fields with DB and cap workout_time
    seen_keys = set()
    by_key = defaultdict(list)  # (sid, date_str) -> list of records
    for rec in data:
        name_key = normalize_name(rec.get("full_name"))

        # Resolve student_id
        sid = rec.get("student_id")
        # Prefer DB mapping by student_id, else by name
        preferred_sid = sid
        if not validate_student_id(preferred_sid):
            # Try DB by name
            candidates = student_by_name.get(name_key, [])
            if candidates:
                preferred_sid = candidates[0]["student_id"]
            else:
                preferred_sid = name_to_preferred.get(name_key) or sid
        else:
            # If multiple IDs for same name, prefer chosen
            preferred_sid = name_to_preferred.get(name_key) or sid

        if preferred_sid != sid:
            rec["student_id"] = preferred_sid

        # Sync block and pe from DB if known
        s_info = student_by_sid.get(rec.get("student_id"))
        if s_info:
            rec["enrolled_block"] = s_info["block_section"] or rec.get("enrolled_block")
            pe = map_pe(s_info["pe_course"]) or rec.get("pe_course")
            rec["pe_course"] = pe

        # Cap by DB minutes if available
        workout_date = rec.get("workout_date")
        db_key = None
        # Convert workout_date MM-DD-YYYY to ISO YYYY-MM-DD for session lookup
        try:
            mm, dd, yyyy = workout_date.split("-")
            iso_date = f"{yyyy}-{mm}-{dd}"
            db_key = (rec.get("student_id"), iso_date)
        except Exception:
            db_key = None

        # Determine target hours
        if db_key and db_key in sessions_by_sid_date:
            minutes = sessions_by_sid_date[db_key]["minutes"]
            sessions = sessions_by_sid_date[db_key]["sessions"]
            hours = minutes / 60.0
            rec["workout_time"] = cap_hours(hours)
            rec["completed_sessions"] = sessions
        else:
            # No DB info; still enforce cap if present
            if rec.get("workout_time") is not None:
                rec["workout_time"] = cap_hours(float(rec["workout_time"]))

        # Recompute error
        errors = []
        if not rec.get("full_name"):
            errors.append("full_name missing")
        sid_val = rec.get("student_id")
        if not validate_student_id(sid_val):
            errors.append(f"invalid student_id '{sid_val}'")
        if rec.get("enrolled_block") is None:
            errors.append("enrolled_block missing")
        pe_val = rec.get("pe_course")
        if pe_val not in {None, "PEDUONE", "PEDUTWO", "PEDUTRI", "PEDUFOR"}:
            errors.append(f"unmapped pe_course '{pe_val}'")
        if errors:
            rec["error"] = "; ".join(errors)
        else:
            rec["error"] = None

        # Index for existence checks
        by_key[(rec.get("student_id"), rec.get("workout_date"))].append(rec)

    # Add missing dates from DB within range
    current = DATE_START
    while current <= DATE_END:
        iso_d = current.isoformat()
        out_d = mmddyyyy(current)
        # For each student with sessions that day, ensure presence
        for (sid, d), agg in sessions_by_sid_date.items():
            if d != iso_d:
                continue
            key = (sid, out_d)
            if key not in by_key:
                # Create a new record from DB
                s_info = student_by_sid.get(sid)
                full_name = s_info["full_name"] if s_info else None
                block = s_info["block_section"] if s_info else None
                pe = map_pe(s_info["pe_course"]) if s_info else None
                new_rec = {
                    "workout_date": out_d,
                    "full_name": full_name,
                    "student_id": sid,
                    "enrolled_block": block,
                    "pe_course": pe,
                    "workout_start": None,
                    "last_gym": None,
                    "workout_end": None,
                    "workout_time": cap_hours(agg["minutes"] / 60.0),
                    "completed_sessions": agg["sessions"],
                    "error": None,
                }
                data.append(new_rec)
                by_key[key].append(new_rec)
        current += timedelta(days=1)

    # Also include raw-log-only days: for each name, if JSON has a day but DB lacked minutes,
    # ensure those days are retained under the preferred/DB-resolved student_id and hours capped at 2.0
    # Build name -> preferred sid (post-reconciliation)
    name_to_sid = {}
    for rec in data:
        n = normalize_name(rec.get("full_name"))
        sid = rec.get("student_id")
        if validate_student_id(sid):
            name_to_sid[n] = sid

    normalized_records = []
    seen_sid_date = set()
    for rec in data:
        n = normalize_name(rec.get("full_name"))
        target_sid = rec.get("student_id")
        if not validate_student_id(target_sid):
            mapped = name_to_sid.get(n)
            if mapped:
                target_sid = mapped
        # Cap time
        wt = rec.get("workout_time")
        if wt is not None:
            rec["workout_time"] = cap_hours(float(wt))
        # Update sid if mapped
        rec["student_id"] = target_sid
        key = (rec.get("student_id"), rec.get("workout_date"))
        if key in seen_sid_date:
            # skip exact duplicates
            continue
        seen_sid_date.add(key)
        normalized_records.append(rec)

    data = normalized_records

    # Write back
    with open(ALL_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()


