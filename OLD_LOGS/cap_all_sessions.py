import sqlite3
import os
from datetime import datetime, timedelta


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")


def cap_all_sessions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Find all sessions with duration > 120 minutes
    cur.execute(
        """
        SELECT id, student_id, check_in_time, check_out_time, duration_minutes, date
        FROM gym_sessions 
        WHERE check_out_time IS NOT NULL 
        AND duration_minutes > 120
        ORDER BY duration_minutes DESC
        """
    )
    long_sessions = cur.fetchall()
    
    print(f"Found {len(long_sessions)} sessions with duration > 120 minutes")
    
    capped_count = 0
    total_minutes_saved = 0
    
    for session_id, student_id, check_in_str, check_out_str, duration_minutes, date in long_sessions:
        # Parse check-in time
        check_in = datetime.fromisoformat(check_in_str)
        
        # Calculate new check-out time (2 hours after check-in)
        new_check_out = check_in + timedelta(minutes=120)
        
        # Calculate minutes saved
        minutes_saved = duration_minutes - 120
        
        # Update the session
        cur.execute(
            """
            UPDATE gym_sessions 
            SET check_out_time = ?, duration_minutes = 120
            WHERE id = ?
            """,
            (new_check_out.isoformat(sep=' '), session_id)
        )
        
        capped_count += 1
        total_minutes_saved += minutes_saved
        
        print(f"Session {session_id}: {duration_minutes}min -> 120min (saved {minutes_saved}min)")
    
    # Update daily stats for affected students/dates
    print("\nUpdating daily stats...")
    cur.execute(
        """
        SELECT student_id, date, SUM(duration_minutes) as total_minutes, COUNT(*) as total_sessions
        FROM gym_sessions 
        WHERE check_out_time IS NOT NULL
        GROUP BY student_id, date
        """
    )
    
    daily_totals = cur.fetchall()
    
    for student_id, date, total_minutes, total_sessions in daily_totals:
        # Update or create daily stats
        cur.execute(
            "SELECT id FROM gym_daily_stats WHERE student_id = ? AND date = ?",
            (student_id, date)
        )
        row = cur.fetchone()
        
        if row:
            cur.execute(
                "UPDATE gym_daily_stats SET total_minutes = ?, total_sessions = ? WHERE id = ?",
                (total_minutes, total_sessions, row[0])
            )
        else:
            cur.execute(
                "INSERT INTO gym_daily_stats (student_id, date, total_minutes, total_sessions) VALUES (?, ?, ?, ?)",
                (student_id, date, total_minutes, total_sessions)
            )
    
    conn.commit()
    conn.close()
    
    print(f"\nCapping completed:")
    print(f"- Sessions capped: {capped_count}")
    print(f"- Total minutes saved: {total_minutes_saved}")
    print(f"- Daily stats updated for {len(daily_totals)} student-date combinations")


def verify_caps():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check for any remaining sessions > 120 minutes
    cur.execute(
        "SELECT COUNT(*) FROM gym_sessions WHERE duration_minutes > 120 AND check_out_time IS NOT NULL"
    )
    remaining_long = cur.fetchone()[0]
    
    # Check total sessions
    cur.execute("SELECT COUNT(*) FROM gym_sessions WHERE check_out_time IS NOT NULL")
    total_sessions = cur.fetchone()[0]
    
    # Check average duration
    cur.execute("SELECT AVG(duration_minutes) FROM gym_sessions WHERE check_out_time IS NOT NULL")
    avg_duration = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\nVerification:")
    print(f"- Total completed sessions: {total_sessions}")
    print(f"- Sessions > 120 minutes remaining: {remaining_long}")
    print(f"- Average session duration: {avg_duration:.2f} minutes")
    
    if remaining_long == 0:
        print("✅ All sessions successfully capped at 120 minutes!")
    else:
        print("⚠️ Some sessions still exceed 120 minutes")


if __name__ == "__main__":
    cap_all_sessions()
    verify_caps()
