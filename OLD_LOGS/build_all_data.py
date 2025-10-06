import json
import os
import re
from datetime import datetime, date, timedelta


DATE_START = date(2025, 8, 1)
DATE_END = date(2025, 8, 31)


def iter_target_filenames(logs_dir: str):

    current = DATE_START
    while current <= DATE_END:
        # support both unpadded and zero-padded filenames
        fname_unpadded = f"{current.month}-{current.day}-{current.year}.json"
        fname_padded = f"{current.strftime('%m')}-{current.strftime('%d')}-{current.year}.json"
        fpath_unpadded = os.path.join(logs_dir, fname_unpadded)
        fpath_padded = os.path.join(logs_dir, fname_padded)
        # Yield padded first to match current files, but process whichever exists
        yield current, (fpath_padded if os.path.exists(fpath_padded) else fpath_unpadded)
        current += timedelta(days=1)


def normalize_student_id(student_id_value):

    if student_id_value is None:
        return None, "student_id missing"

    if not isinstance(student_id_value, str):
        student_id_value = str(student_id_value)

    normalized = student_id_value.strip()
    normalized = re.sub(r"\s+", "", normalized)

    # Accept exactly 4 digits, hyphen, 6 digits, and starting with 20
    if re.fullmatch(r"20\d{2}-\d{6}", normalized):
        return normalized, None

    return None, f"invalid student_id '{student_id_value}'"


def map_pe_course(value):

    if value is None:
        return None, "pe_course missing"

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
        return mapping[key], None

    # treat common variants like 'pedu1', 'none' etc.
    if key.startswith("PEDU") and key[4:] in {"1", "2", "3", "4"}:
        return mapping.get(f"PEDU{key[4:]}", None), None

    if key in {"NONE", "N/A", "NA", "NULL", ""}:
        return None, None

    return "INVALID", f"unmapped pe_course '{value}'"


def ensure_time_format(value, field_name):

    if value is None:
        return None, f"{field_name} missing"

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    # Expect HH:MM:SS with HH in 00-23
    if re.fullmatch(r"(0\d|1\d|2[0-3]|\d):[0-5]\d:[0-5]\d", value):
        # If single-digit hour, pad to two digits
        parts = value.split(":")
        hh = parts[0].zfill(2)
        return f"{hh}:{parts[1]}:{parts[2]}", None

    return None, f"invalid {field_name} '{value}'"


def parse_float(value, field_name):

    if value is None:
        return None, f"{field_name} missing"
    try:
        return float(value), None
    except Exception:
        return None, f"invalid {field_name} '{value}'"


def parse_int(value, field_name):

    if value is None:
        return None, f"{field_name} missing"
    try:
        # Some inputs may be floats like 2.0, coerce safely
        iv = int(float(value))
        return iv, None
    except Exception:
        return None, f"invalid {field_name} '{value}'"


def build_record(raw: dict, workout_date_str: str):

    errors = []

    full_name = raw.get("full_name") if isinstance(raw.get("full_name"), str) else None
    if full_name is None:
        errors.append("full_name missing")

    student_id, err = normalize_student_id(raw.get("student_id"))
    if err:
        errors.append(err)

    enrolled_block = raw.get("enrolled_block") if isinstance(raw.get("enrolled_block"), str) else None
    if enrolled_block is None:
        errors.append("enrolled_block missing")

    pe_course, pe_err = map_pe_course(raw.get("pe_course"))
    if pe_err:
        errors.append(pe_err)

    workout_start, ws_err = ensure_time_format(raw.get("workout_start"), "workout_start")
    if ws_err:
        errors.append(ws_err)

    last_gym_value = raw.get("last_gym")
    if last_gym_value is not None and not isinstance(last_gym_value, str):
        last_gym_value = str(last_gym_value)

    workout_end, we_err = ensure_time_format(raw.get("workout_end"), "workout_end")
    if we_err:
        errors.append(we_err)

    workout_time_val, wt_err = parse_float(raw.get("workout_time"), "workout_time")
    if wt_err:
        errors.append(wt_err)
    # Convert minutes to hours if present
    if workout_time_val is not None:
        workout_time_val = workout_time_val / 60.0

    completed_sessions_val, cs_err = parse_int(raw.get("completed_sessions"), "completed_sessions")
    if cs_err:
        errors.append(cs_err)

    record = {
        "workout_date": workout_date_str,
        "full_name": full_name,
        "student_id": student_id,
        "enrolled_block": enrolled_block,
        "pe_course": pe_course,
        "workout_start": workout_start,
        "last_gym": last_gym_value if last_gym_value is not None else None,
        "workout_end": workout_end,
        "workout_time": workout_time_val,
        "completed_sessions": completed_sessions_val,
        "error": None if not errors else "; ".join(errors),
    }

    return record


def main():

    logs_dir = os.path.dirname(__file__)
    all_records = []

    for current_date, fpath in iter_target_filenames(logs_dir):
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            # If the entire file fails to parse, preserve an error stub
            all_records.append({
                "workout_date": current_date.strftime("%m-%d-%Y"),
                "full_name": None,
                "student_id": None,
                "enrolled_block": None,
                "pe_course": None,
                "workout_start": None,
                "last_gym": None,
                "workout_end": None,
                "workout_time": None,
                "completed_sessions": None,
                "error": f"file parse error: {e}",
            })
            continue

        workout_date_str = current_date.strftime("%m-%d-%Y")

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    all_records.append({
                        "workout_date": workout_date_str,
                        "full_name": None,
                        "student_id": None,
                        "enrolled_block": None,
                        "pe_course": None,
                        "workout_start": None,
                        "last_gym": None,
                        "workout_end": None,
                        "workout_time": None,
                        "completed_sessions": None,
                        "error": "malformed record (not an object)",
                    })
                    continue
                record = build_record(item, workout_date_str)
                all_records.append(record)
        else:
            all_records.append({
                "workout_date": workout_date_str,
                "full_name": None,
                "student_id": None,
                "enrolled_block": None,
                "pe_course": None,
                "workout_start": None,
                "last_gym": None,
                "workout_end": None,
                "workout_time": None,
                "completed_sessions": None,
                "error": "file root is not an array",
            })

    out_path = os.path.join(logs_dir, "ALL_DATA.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()


