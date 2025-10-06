import csv
import json
import os
import re


LOGS_DIR = os.path.dirname(__file__)
INPUT_PATH = os.path.join(LOGS_DIR, "ALL_DATA.json")
OUTPUT_PATH = os.path.join(LOGS_DIR, "ALL_DATA_AUDIT.csv")


def is_valid_student_id(sid: str) -> bool:
    return bool(sid) and re.fullmatch(r"20\d{2}-\d{6}", str(sid)) is not None


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Heuristic flags
    def is_added_from_db(rec):
        # Likely added purely from DB aggregates (no raw times present)
        return (
            rec.get("workout_start") in (None, "") and
            rec.get("workout_end") in (None, "") and
            rec.get("last_gym") in (None, "")
        )

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "workout_date",
            "full_name",
            "student_id",
            "enrolled_block",
            "pe_course",
            "workout_time",
            "completed_sessions",
            "error",
            "capped_time",
            "added_from_db",
            "valid_student_id",
        ])

        for rec in data:
            wt = rec.get("workout_time")
            capped = (wt is not None and float(wt) >= 2.0)
            added = is_added_from_db(rec)
            valid_sid = is_valid_student_id(rec.get("student_id"))

            writer.writerow([
                rec.get("workout_date"),
                rec.get("full_name"),
                rec.get("student_id"),
                rec.get("enrolled_block"),
                rec.get("pe_course"),
                wt,
                rec.get("completed_sessions"),
                rec.get("error"),
                int(capped),
                int(added),
                int(valid_sid),
            ])

    print(f"Wrote audit CSV to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()


