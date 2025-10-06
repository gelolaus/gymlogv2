#!/usr/bin/env python
"""
Migration script for Wilte V. Dela Cruz's gym data.
This script imports gym session data from old logs specifically for student ID: 1364078561

Usage:
    python migrate_wilte_data.py

Requirements:
    - Run this in the Django project directory
    - Student must already be registered in the system
    - Will create gym sessions and daily stats
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymlog_backend.settings')
django.setup()

from gym_app.models import Student, GymSession, DailyGymStats
from django.db import transaction


class WilteMigration:
    def __init__(self):
        self.student_id = "2024-140258"
        self.full_name = "Wilte V. Dela Cruz"
        self.student = None
        
        # Define Wilte's gym session data from old logs
        # Note: Using start/end times for accurate duration calculation
        # The stored workout_time values in old logs appear to be inconsistent
        self.session_data = [
            {
                'date': date(2025, 8, 11),
                'start_time': '09:32:45',
                'end_time': '20:34:32',
                'note': 'Long session - ~11 hours'
            },
            {
                'date': date(2025, 8, 15),
                'start_time': '10:55:24',
                'end_time': '10:55:39',
                'note': 'Very short session - 15 seconds'
            },
            {
                'date': date(2025, 8, 15),
                'start_time': '10:55:44',
                'end_time': '18:13:53',
                'note': 'Normal session - ~7.3 hours'
            }
        ]
    
    def run_migration(self):
        """Main migration function"""
        print(f"🔍 Looking for student: {self.full_name} (ID: {self.student_id})")
        
        # Find the student (should already be registered)
        try:
            self.student = Student.objects.get(student_id=self.student_id)
            print(f"✅ Found student: {self.student.full_name}")
        except Student.DoesNotExist:
            print(f"❌ ERROR: Student with ID {self.student_id} not found!")
            print("   Please make sure Wilte has registered in the new system first.")
            return False
        
        # Check if sessions already exist
        existing_sessions = GymSession.objects.filter(student=self.student)
        if existing_sessions.exists():
            print(f"⚠️  WARNING: Student already has {existing_sessions.count()} gym sessions.")
            response = input("Do you want to continue and add more sessions? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False
        
        # Import sessions
        success_count = 0
        total_sessions = len(self.session_data)
        
        print(f"\n📥 Importing {total_sessions} gym sessions...")
        
        with transaction.atomic():
            for i, session_info in enumerate(self.session_data, 1):
                print(f"\n[{i}/{total_sessions}] Processing session for {session_info['date']}...")
                
                success = self.create_gym_session(session_info)
                if success:
                    success_count += 1
                    print(f"  ✅ Session created successfully")
                else:
                    print(f"  ⚠️  Session skipped (duplicate or error)")
        
        # Update daily stats for all dates
        print(f"\n📊 Updating daily statistics...")
        dates_to_update = list(set(session['date'] for session in self.session_data))
        for session_date in dates_to_update:
            DailyGymStats.update_daily_stats(self.student, session_date)
            print(f"  ✅ Updated stats for {session_date}")
        
        # Print summary
        print(f"\n🎉 Migration completed!")
        print(f"  📈 Sessions imported: {success_count}/{total_sessions}")
        print(f"  👤 Student: {self.student.full_name}")
        print(f"  📅 Dates covered: {min(dates_to_update)} to {max(dates_to_update)}")
        
        # Show final stats
        total_sessions_count = self.student.total_gym_sessions
        total_time_minutes = self.student.total_gym_time_minutes
        print(f"  ⏱️  Total gym time: {total_time_minutes} minutes ({total_time_minutes//60}h {total_time_minutes%60}m)")
        print(f"  🏃 Total sessions: {total_sessions_count}")
        
        return True
    
    def create_gym_session(self, session_info):
        """Create a single gym session"""
        try:
            # Parse times
            session_date = session_info['date']
            start_time = datetime.strptime(session_info['start_time'], '%H:%M:%S').time()
            end_time = datetime.strptime(session_info['end_time'], '%H:%M:%S').time()
            
            # Create datetime objects
            start_datetime = datetime.combine(session_date, start_time)
            end_datetime = datetime.combine(session_date, end_time)
            
            # Handle overnight sessions (end time next day)
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            # Convert to timezone-aware datetimes
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
            
            # Calculate duration
            duration_seconds = (end_datetime - start_datetime).total_seconds()
            duration_minutes = int(duration_seconds / 60)
            
            # Check for duplicates
            existing = GymSession.objects.filter(
                student=self.student,
                date=session_date,
                check_in_time=start_datetime,
            ).first()
            
            if existing:
                print(f"    ⚠️  Duplicate session found, skipping...")
                return False
            
            # Create the session
            session = GymSession.objects.create(
                student=self.student,
                check_in_time=start_datetime,
                check_out_time=end_datetime,
                duration_minutes=duration_minutes,
                date=session_date,
                is_active=False  # All migrated sessions are completed
            )
            
            print(f"    📝 Created session: {start_time} - {end_time} ({duration_minutes} min)")
            return True
            
        except Exception as e:
            print(f"    ❌ Error creating session: {str(e)}")
            return False


def main():
    print("=" * 60)
    print("🏋️  WILTE V. DELA CRUZ - GYM DATA MIGRATION")
    print("=" * 60)
    print()
    print("This script will migrate gym session data for:")
    print(f"  👤 Name: Wilte V. Dela Cruz")
    print(f"  🆔 Student ID: 1364078561")
    print(f"  📅 Sessions: 3 sessions from August 11-15, 2025")
    print()
    
    # Confirm before proceeding
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Run migration
    migration = WilteMigration()
    success = migration.run_migration()
    
    if success:
        print(f"\n✅ Migration completed successfully!")
        print(f"   Wilte's gym data has been imported to the database.")
    else:
        print(f"\n❌ Migration failed or was cancelled.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
