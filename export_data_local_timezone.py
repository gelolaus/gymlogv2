#!/usr/bin/env python
"""
Enhanced data export script for Gym Log system with proper timezone handling.
This script exports data with timestamps converted to your local timezone (Asia/Manila).

Usage:
    python export_data_local_timezone.py [options]

Options:
    --format [csv|json]     Output format (default: csv)
    --type [sessions|daily|students]  Data type to export (default: sessions)
    --student-id ID         Filter by specific student ID
    --date-from YYYY-MM-DD  Start date filter
    --date-to YYYY-MM-DD    End date filter
    --output-file FILENAME  Output filename (auto-generated if not provided)

Examples:
    python export_data_local_timezone.py --type sessions --format csv
    python export_data_local_timezone.py --type sessions --student-id 2023-123456
    python export_data_local_timezone.py --type daily --date-from 2024-01-01 --date-to 2024-01-31
"""

import os
import django
import argparse
import csv
import json
from datetime import datetime, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymlog_backend.settings')
django.setup()

from gym_app.timezone_utils import (
    export_gym_sessions_with_local_time,
    export_daily_stats_with_local_time,
    format_datetime_local,
    get_local_timezone
)
from gym_app.models import Student
from django.utils import timezone


def export_students_data():
    """Export all students with local registration timestamps"""
    students = Student.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    student_data = []
    for student in students:
        student_data.append({
            'id': student.id,
            'student_id': student.student_id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'full_name': student.full_name,
            'pe_course': student.pe_course,
            'block_section': student.block_section,
            'rfid': student.rfid,
            'registration_date_utc': student.registration_date.isoformat() if student.registration_date else None,
            'registration_date_local': format_datetime_local(student.registration_date) if student.registration_date else None,
            'total_gym_sessions': student.total_gym_sessions,
            'total_gym_time_minutes': student.total_gym_time_minutes,
            'total_gym_time_hours': round(student.total_gym_time_minutes / 60, 2) if student.total_gym_time_minutes else 0
        })
    
    return student_data


def save_to_csv(data, filename, data_type):
    """Save data to CSV with appropriate headers"""
    if not data:
        print(f"No {data_type} data to export.")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Add timezone info header comment
        csvfile.write(f"# Data exported on {timezone.localtime(timezone.now())} ({get_local_timezone()})\n")
        csvfile.write(f"# All local timestamps are in {get_local_timezone()} timezone\n")
        
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Exported {len(data)} {data_type} records to {filename}")


def save_to_json(data, filename, data_type):
    """Save data to JSON with metadata"""
    export_metadata = {
        'export_timestamp': timezone.localtime(timezone.now()).isoformat(),
        'timezone': str(get_local_timezone()),
        'record_count': len(data),
        'data_type': data_type,
        'note': 'All timestamps ending with "_local" are converted to the specified timezone'
    }
    
    output = {
        'metadata': export_metadata,
        'data': data
    }
    
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(output, jsonfile, indent=2, default=str)
    
    print(f"Exported {len(data)} {data_type} records to {filename}")


def generate_filename(data_type, format_type, student_id=None, date_from=None, date_to=None):
    """Generate appropriate filename based on export parameters"""
    timestamp = timezone.localtime(timezone.now()).strftime('%Y%m%d_%H%M%S')
    
    base_name = f"gym_{data_type}_export"
    
    filters = []
    if student_id:
        filters.append(f"student_{student_id}")
    if date_from:
        filters.append(f"from_{date_from}")
    if date_to:
        filters.append(f"to_{date_to}")
    
    if filters:
        base_name += "_" + "_".join(filters)
    
    return f"{base_name}_{timestamp}.{format_type}"


def parse_date(date_string):
    """Parse date string and return date object"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        print(f"Invalid date format: {date_string}. Use YYYY-MM-DD format.")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Export Gym Log data with proper timezone conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --type sessions --format csv
  %(prog)s --type sessions --student-id 2023-123456
  %(prog)s --type daily --date-from 2024-01-01 --date-to 2024-01-31
  %(prog)s --type students --format json
        """
    )
    
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Output format (default: csv)')
    parser.add_argument('--type', choices=['sessions', 'daily', 'students'], default='sessions',
                       help='Data type to export (default: sessions)')
    parser.add_argument('--student-id', help='Filter by specific student ID')
    parser.add_argument('--date-from', help='Start date filter (YYYY-MM-DD)')
    parser.add_argument('--date-to', help='End date filter (YYYY-MM-DD)')
    parser.add_argument('--output-file', help='Output filename (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    # Parse dates if provided
    date_from = parse_date(args.date_from) if args.date_from else None
    date_to = parse_date(args.date_to) if args.date_to else None
    
    if args.date_from and not date_from:
        return
    if args.date_to and not date_to:
        return
    
    # Generate filename if not provided
    filename = args.output_file or generate_filename(
        args.type, args.format, args.student_id, date_from, date_to
    )
    
    print(f"Exporting {args.type} data in {args.format} format...")
    print(f"Local timezone: {get_local_timezone()}")
    
    # Export data based on type
    if args.type == 'sessions':
        data = export_gym_sessions_with_local_time(
            student_id=args.student_id,
            date_from=date_from,
            date_to=date_to
        )
    elif args.type == 'daily':
        data = export_daily_stats_with_local_time(
            date_from=date_from,
            date_to=date_to
        )
    elif args.type == 'students':
        data = export_students_data()
    
    # Save data
    if args.format == 'csv':
        save_to_csv(data, filename, args.type)
    else:
        save_to_json(data, filename, args.type)
    
    print(f"Export completed successfully!")
    
    # Show sample of exported data
    if data:
        print(f"\nSample record:")
        if args.format == 'json':
            print(json.dumps(data[0], indent=2, default=str))
        else:
            for key, value in list(data[0].items())[:5]:  # Show first 5 fields
                print(f"  {key}: {value}")
            if len(data[0]) > 5:
                print(f"  ... and {len(data[0]) - 5} more fields")


if __name__ == '__main__':
    main()

