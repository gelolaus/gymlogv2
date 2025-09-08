"""
Timezone utility functions for proper datetime handling in the Gym Log application.
Use these functions when extracting data to ensure times are displayed in the correct timezone.
"""

from django.utils import timezone
from django.conf import settings
import sqlite3
from datetime import datetime
import pytz


def get_local_timezone():
    """Get the configured local timezone"""
    return pytz.timezone(settings.TIME_ZONE)


def convert_utc_to_local(utc_datetime):
    """
    Convert UTC datetime to local timezone.
    
    Args:
        utc_datetime: datetime object in UTC or datetime string
    
    Returns:
        datetime object in local timezone
    """
    if isinstance(utc_datetime, str):
        # Parse string datetime (assuming it's from database)
        utc_datetime = datetime.fromisoformat(utc_datetime.replace('Z', '+00:00'))
    
    if utc_datetime.tzinfo is None:
        # Assume UTC if no timezone info
        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)
    
    return timezone.localtime(utc_datetime)


def format_datetime_local(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """
    Format datetime in local timezone.
    
    Args:
        dt: datetime object
        format_string: strftime format string
    
    Returns:
        formatted datetime string in local timezone
    """
    local_dt = convert_utc_to_local(dt)
    return local_dt.strftime(format_string)


def export_gym_sessions_with_local_time(student_id=None, date_from=None, date_to=None):
    """
    Export gym sessions with properly converted local timestamps.
    
    Args:
        student_id: Filter by student ID (optional)
        date_from: Start date filter (optional)
        date_to: End date filter (optional)
    
    Returns:
        List of dictionaries with session data in local timezone
    """
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Base query
    query = """
    SELECT 
        gs.id,
        s.student_id,
        s.first_name,
        s.last_name,
        gs.check_in_time,
        gs.check_out_time,
        gs.duration_minutes,
        gs.date,
        gs.is_active
    FROM gym_sessions gs
    JOIN gym_students s ON gs.student_id = s.id
    WHERE 1=1
    """
    
    params = []
    
    # Add filters
    if student_id:
        query += " AND s.student_id = ?"
        params.append(student_id)
    
    if date_from:
        query += " AND gs.date >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND gs.date <= ?"
        params.append(date_to)
    
    query += " ORDER BY gs.check_in_time DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries with local timestamps
    sessions = []
    for row in rows:
        session = {
            'id': row[0],
            'student_id': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'check_in_time_utc': row[4],
            'check_out_time_utc': row[5],
            'check_in_time_local': format_datetime_local(row[4]) if row[4] else None,
            'check_out_time_local': format_datetime_local(row[5]) if row[5] else None,
            'duration_minutes': row[6],
            'date': row[7],
            'is_active': bool(row[8])
        }
        sessions.append(session)
    
    return sessions


def export_daily_stats_with_local_time(date_from=None, date_to=None):
    """
    Export daily statistics with local timezone context.
    
    Args:
        date_from: Start date filter (optional)
        date_to: End date filter (optional)
    
    Returns:
        List of dictionaries with daily stats
    """
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    query = """
    SELECT 
        ds.date,
        s.student_id,
        s.first_name,
        s.last_name,
        ds.total_sessions,
        ds.total_minutes
    FROM gym_daily_stats ds
    JOIN gym_students s ON ds.student_id = s.id
    WHERE 1=1
    """
    
    params = []
    
    if date_from:
        query += " AND ds.date >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND ds.date <= ?"
        params.append(date_to)
    
    query += " ORDER BY ds.date DESC, s.last_name, s.first_name"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    stats = []
    for row in rows:
        stat = {
            'date': row[0],
            'student_id': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'total_sessions': row[4],
            'total_minutes': row[5],
            'total_hours': round(row[5] / 60, 2) if row[5] else 0
        }
        stats.append(stat)
    
    return stats


def create_timezone_aware_csv_export(sessions_data, filename_prefix='gym_export'):
    """
    Create a CSV export with timezone-aware data.
    
    Args:
        sessions_data: List of session dictionaries from export functions
        filename_prefix: Prefix for the filename
    
    Returns:
        CSV filename with timestamp
    """
    import csv
    from datetime import datetime
    
    # Create filename with local timestamp
    local_now = timezone.localtime(timezone.now())
    timestamp = local_now.strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    if not sessions_data:
        return filename
    
    # Write CSV with proper headers
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        if 'student_id' in sessions_data[0]:  # Session data
            fieldnames = [
                'id', 'student_id', 'first_name', 'last_name',
                'check_in_time_local', 'check_out_time_local',
                'duration_minutes', 'date', 'is_active'
            ]
        else:  # Daily stats data
            fieldnames = [
                'date', 'student_id', 'first_name', 'last_name',
                'total_sessions', 'total_minutes', 'total_hours'
            ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in sessions_data:
            # Only write fields that exist in fieldnames
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)
    
    return filename


# Example usage functions
def print_recent_sessions_local_time(limit=10):
    """Print recent sessions with local timestamps for debugging"""
    sessions = export_gym_sessions_with_local_time()[:limit]
    
    print(f"\n=== RECENT {limit} GYM SESSIONS (LOCAL TIME: {settings.TIME_ZONE}) ===")
    for session in sessions:
        print(f"ID: {session['id']}")
        print(f"Student: {session['student_id']} - {session['first_name']} {session['last_name']}")
        print(f"Check-in:  {session['check_in_time_local']} (Local)")
        print(f"Check-out: {session['check_out_time_local']} (Local)")
        print(f"Duration: {session['duration_minutes']} minutes")
        print(f"Date: {session['date']}")
        print("-" * 50)


def generate_timezone_comparison_report():
    """Generate a report showing UTC vs Local time differences"""
    sessions = export_gym_sessions_with_local_time()[:5]
    
    print(f"\n=== TIMEZONE COMPARISON REPORT ===")
    print(f"Configured Timezone: {settings.TIME_ZONE}")
    print(f"Current Local Time: {timezone.localtime(timezone.now())}")
    print(f"Current UTC Time: {timezone.now()}")
    print("\nRecent Sessions - UTC vs Local:")
    
    for session in sessions:
        print(f"\nStudent: {session['student_id']}")
        print(f"  UTC Time:   {session['check_in_time_utc']}")
        print(f"  Local Time: {session['check_in_time_local']}")

