import json
import os
import sqlite3
from datetime import datetime, timedelta


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")
LOGS_DIR = os.path.dirname(__file__)


def normalize_student_id(student_id_value):
    if student_id_value is None:
        return None
    if not isinstance(student_id_value, str):
        student_id_value = str(student_id_value)
    normalized = student_id_value.strip()
    normalized = normalized.replace(" ", "")
    return normalized


def map_pe_course(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    key = value.strip().upper()
    mapping = {
        "PEDU1": "PEDUONE",
        "PEDU2": "PEDUTWO", 
        "PEDU3": "PEDUTRI",
        "PEDU4": "PEDUFOR",
    }
    if key in mapping:
        return mapping[key]
    if key.startswith("PEDU") and key[4:] in {"1", "2", "3", "4"}:
        return mapping.get(f"PEDU{key[4:]}", None)
    if key in {"NONE", "N/A", "NA", "NULL", ""}:
        return "N/A"
    return "N/A"


def ensure_student_exists(cur, student_id, full_name, pe_course, block_section):
    # Check if student exists
    cur.execute("SELECT id FROM gym_students WHERE student_id = ?", (student_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    # Create new student
    cur.execute(
        """
        INSERT INTO gym_students (student_id, first_name, last_name, pe_course, block_section, is_active, registration_date)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        """,
        (student_id, full_name.split()[0] if full_name else "", 
         full_name.split()[-1] if full_name and len(full_name.split()) > 1 else "",
         pe_course, block_section, datetime.now().isoformat())
    )
    return cur.lastrowid


def import_log_file(log_path, target_date):
    with open(log_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys=ON")
    
    imported_sessions = 0
    for record in records:
        student_id = normalize_student_id(record.get("student_id"))
        if not student_id:
            continue
            
        full_name = record.get("full_name", "")
        pe_course = map_pe_course(record.get("pe_course"))
        block_section = (record.get("enrolled_block") or "").upper()
        
        # Ensure student exists
        student_pk = ensure_student_exists(cur, student_id, full_name, pe_course, block_section)
        
        # Parse workout times
        workout_time_minutes = float(record.get("workout_time", 0))
        completed_sessions = int(record.get("completed_sessions", 1))
        
        # Cap at 120 minutes (2 hours)
        workout_time_minutes = min(workout_time_minutes, 120)
        
        # Create synthetic session at midday
        check_in = datetime.fromisoformat(target_date + "T12:00:00")
        check_out = check_in + timedelta(minutes=workout_time_minutes)
        
        cur.execute(
            """
            INSERT INTO gym_sessions (student_id, check_in_time, check_out_time, duration_minutes, date, is_active)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (student_pk, check_in.isoformat(sep=' '), check_out.isoformat(sep=' '), 
             int(workout_time_minutes), target_date)
        )
        
        # Update daily stats
        cur.execute(
            "SELECT id, total_sessions, total_minutes FROM gym_daily_stats WHERE student_id=? AND date=?",
            (student_pk, target_date)
        )
        row = cur.fetchone()
        if row:
            stat_id, sess, mins = row
            cur.execute(
                "UPDATE gym_daily_stats SET total_sessions=?, total_minutes=? WHERE id=?",
                (int(sess or 0) + completed_sessions, int(mins or 0) + int(workout_time_minutes), stat_id)
            )
        else:
            cur.execute(
                "INSERT INTO gym_daily_stats (student_id, date, total_sessions, total_minutes) VALUES (?, ?, ?, ?)",
                (student_pk, target_date, completed_sessions, int(workout_time_minutes))
            )
        
        imported_sessions += 1
    
    conn.commit()
    conn.close()
    return imported_sessions


def main():
    # Import September 2, 2025
    sept2_path = os.path.join(LOGS_DIR, "09-02-2025.json")
    sept2_sessions = import_log_file(sept2_path, "2025-09-02")
    print(f"Imported {sept2_sessions} sessions for September 2, 2025")
    
    # Import September 5, 2025  
    sept5_path = os.path.join(LOGS_DIR, "09-05-2025.json")
    sept5_sessions = import_log_file(sept5_path, "2025-09-05")
    print(f"Imported {sept5_sessions} sessions for September 5, 2025")
    
    print(f"Total imported: {sept2_sessions + sept5_sessions} sessions")


if __name__ == "__main__":
    main()
