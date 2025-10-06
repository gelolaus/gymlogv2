import os
import sqlite3


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")


def main(cutoff: str = "2025-10-05") -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM gym_sessions WHERE is_active=1 AND check_out_time IS NULL AND date<=?",
        (cutoff,),
    )
    remaining = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM gym_daily_stats")
    stats_count = cur.fetchone()[0]

    print("Cutoff:", cutoff)
    print("Remaining open sessions <= cutoff:", remaining)
    print("Total daily stats rows:", stats_count)

    conn.close()


if __name__ == "__main__":
    main()


