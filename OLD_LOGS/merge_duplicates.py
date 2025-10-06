import os
import re
import sqlite3
from collections import defaultdict


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")


def normalize_name(first: str, last: str) -> str:
    f = (first or "").strip().lower()
    l = (last or "").strip().lower()
    return f"{l}::{f}"


def id_score(student_id: str) -> tuple:
    if not student_id:
        return (3, )
    if re.fullmatch(r"^202\d-(140|040)\d{3}$", student_id):
        return (0, )
    if re.fullmatch(r"^20\d{2}-\d{6}$", student_id):
        return (1, )
    return (2, )


def choose_primary(rows):
    # rows: list of dict(id, student_id, first_name, last_name, rfid, pe_course, block_section, registration_date)
    # Prefer best student_id pattern; tie-breaker: has RFID; tie: most recent registration_date; tie: smallest id
    def key(r):
        score = id_score(r["student_id"]) + (
            0 if r["rfid"] else 1,
            # newer first (descending), so use negative timestamp string if available
            r["registration_date"] or "",
            r["id"],
        )
        return score

    # We want minimal score tuple; but registration_date as text sorts ascending; we will invert by padding? Simpler: leave as is; id_score and RFID should suffice.
    rows_sorted = sorted(rows, key=key)
    return rows_sorted[0]


def merge_daily_stats(cur, primary_id, duplicate_id):
    # Repoint duplicates while preserving unique (student,date). Merge totals when needed.
    cur.execute(
        "SELECT date, total_sessions, total_minutes FROM gym_daily_stats WHERE student_id=?",
        (duplicate_id,),
    )
    dup_stats = cur.fetchall()
    for date_val, total_sessions, total_minutes in dup_stats:
        # Does primary already have this date?
        cur.execute(
            "SELECT id, total_sessions, total_minutes FROM gym_daily_stats WHERE student_id=? AND date=?",
            (primary_id, date_val),
        )
        row = cur.fetchone()
        if row:
            stat_id, psess, pmin = row
            new_sessions = (psess or 0) + (total_sessions or 0)
            new_minutes = (pmin or 0) + (total_minutes or 0)
            cur.execute(
                "UPDATE gym_daily_stats SET total_sessions=?, total_minutes=? WHERE id=?",
                (new_sessions, new_minutes, stat_id),
            )
            cur.execute(
                "DELETE FROM gym_daily_stats WHERE student_id=? AND date=?",
                (duplicate_id, date_val),
            )
        else:
            cur.execute(
                "UPDATE gym_daily_stats SET student_id=? WHERE student_id=? AND date=?",
                (primary_id, duplicate_id, date_val),
            )


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys=ON")

    # Load all students
    cur.execute(
        """
        SELECT id, student_id, first_name, last_name, pe_course, block_section, rfid, registration_date
        FROM gym_students
        """
    )
    rows = cur.fetchall()

    # Group by normalized name
    by_name = defaultdict(list)
    for r in rows:
        rid, sid, first, last, pe, block, rfid, reg = r
        by_name[normalize_name(first, last)].append({
            "id": rid,
            "student_id": sid,
            "first_name": first,
            "last_name": last,
            "pe_course": pe,
            "block_section": block,
            "rfid": rfid,
            "registration_date": reg,
        })

    merged_count = 0
    for name_key, group in by_name.items():
        if len(group) <= 1:
            continue

        # Choose primary
        primary = choose_primary(group)
        primary_id = primary["id"]

        # Consolidate best pe_course and block_section into primary
        best_pe = primary["pe_course"]
        best_block = primary["block_section"]
        best_rfid = primary["rfid"]
        for g in group:
            # Prefer a concrete PE over 'N/A'
            if g["pe_course"] and g["pe_course"] != 'N/A' and (best_pe == 'N/A' or not best_pe):
                best_pe = g["pe_course"]
            if g["block_section"] and not best_block:
                best_block = g["block_section"]
            if g["rfid"] and not best_rfid:
                best_rfid = g["rfid"]

        cur.execute(
            "UPDATE gym_students SET pe_course=?, block_section=?, rfid=? WHERE id=?",
            (best_pe, best_block, best_rfid, primary_id),
        )

        # Merge others into primary
        for g in group:
            if g["id"] == primary_id:
                continue
            dup_id = g["id"]

            # Repoint gym_sessions
            cur.execute(
                "UPDATE gym_sessions SET student_id=? WHERE student_id=?",
                (primary_id, dup_id),
            )

            # Merge daily stats
            merge_daily_stats(cur, primary_id, dup_id)

            # Delete duplicate student
            cur.execute("DELETE FROM gym_students WHERE id=?", (dup_id,))
            merged_count += 1

    conn.commit()
    conn.close()
    print(f"Merged {merged_count} duplicate student records.")


if __name__ == "__main__":
    main()


