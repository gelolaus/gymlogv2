#!/usr/bin/env python
"""
Development setup script for APC Gym Log System
This script helps set up the development environment and creates sample data.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from random import randint, choice

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymlog_backend.settings')
django.setup()

from gym_app.models import Student, GymSession, DailyGymStats
from django.utils import timezone


def create_sample_students():
    """Create sample students for testing"""
    print("Creating sample students...")
    
    sample_students = [
        {
            'student_id': '2023-123456',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'pe_course': 'PEDUONE',
            'block_section': 'STEM241'
        },
        {
            'student_id': '2023-234567',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'pe_course': 'PEDUTWO',
            'block_section': 'CS231'
        },
        {
            'student_id': '2023-345678',
            'first_name': 'Jose',
            'last_name': 'Rizal',
            'pe_course': 'PEDUTRI',
            'block_section': 'SF251'
        },
        {
            'student_id': '2022-456789',
            'first_name': 'Ana',
            'last_name': 'Garcia',
            'pe_course': 'PEDUFOR',
            'block_section': 'BMMA223'
        },
        {
            'student_id': '2024-567890',
            'first_name': 'Miguel',
            'last_name': 'Rodriguez',
            'pe_course': 'N/A',
            'block_section': 'STEM242'
        }
    ]
    
    created_students = []
    for student_data in sample_students:
        student, created = Student.objects.get_or_create(
            student_id=student_data['student_id'],
            defaults=student_data
        )
        if created:
            print(f"✓ Created student: {student.full_name} ({student.student_id})")
        else:
            print(f"○ Student already exists: {student.full_name} ({student.student_id})")
        created_students.append(student)
    
    return created_students


def create_sample_gym_sessions(students):
    """Create sample gym sessions for the past 30 days"""
    print("\nCreating sample gym sessions...")
    
    now = timezone.now()
    sessions_created = 0
    
    for student in students:
        # Create sessions for the past 30 days with varying frequency
        for days_ago in range(30):
            date = now - timedelta(days=days_ago)
            
            # Some students are more active than others
            activity_probability = {
                '2023-123456': 0.8,  # Very active
                '2023-234567': 0.6,  # Moderately active
                '2023-345678': 0.4,  # Less active
                '2022-456789': 0.7,  # Active
                '2024-567890': 0.3,  # Occasional
            }
            
            # Random chance to have a session on this day
            if randint(1, 100) <= (activity_probability.get(student.student_id, 0.5) * 100):
                # Random session duration between 30-120 minutes
                duration = randint(30, 120)
                
                # Create check-in time (random hour between 6 AM and 8 PM)
                check_in_hour = randint(6, 20)
                check_in_minute = randint(0, 59)
                
                check_in_time = date.replace(
                    hour=check_in_hour,
                    minute=check_in_minute,
                    second=0,
                    microsecond=0
                )
                
                check_out_time = check_in_time + timedelta(minutes=duration)
                
                # Create the session
                session = GymSession.objects.create(
                    student=student,
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    duration_minutes=duration,
                    date=check_in_time.date(),
                    is_active=False
                )
                
                # Update daily stats
                DailyGymStats.update_daily_stats(student, session.date)
                sessions_created += 1
    
    print(f"✓ Created {sessions_created} sample gym sessions")


def create_active_sessions(students):
    """Create some active sessions for testing real-time features"""
    print("\nCreating active sessions...")
    
    # Make 1-2 students currently active
    active_students = students[:2]
    
    for student in active_students:
        # Check if already has active session
        if not GymSession.objects.filter(student=student, is_active=True).exists():
            # Create active session that started 15-60 minutes ago
            minutes_ago = randint(15, 60)
            check_in_time = timezone.now() - timedelta(minutes=minutes_ago)
            
            session = GymSession.objects.create(
                student=student,
                check_in_time=check_in_time,
                date=check_in_time.date(),
                is_active=True
            )
            
            print(f"✓ Created active session for {student.full_name} (started {minutes_ago} minutes ago)")


def main():
    """Main setup function"""
    print("🏃‍♂️ APC Gym Log System - Development Setup")
    print("=" * 50)
    
    try:
        # Create sample students
        students = create_sample_students()
        
        # Create historical gym sessions
        create_sample_gym_sessions(students)
        
        # Create some active sessions
        create_active_sessions(students)
        
        print("\n" + "=" * 50)
        print("✅ Development setup completed successfully!")
        print("\nSample students created:")
        for student in students:
            sessions_count = student.gym_sessions.count()
            active_session = student.gym_sessions.filter(is_active=True).first()
            status = "🔴 ACTIVE" if active_session else "⭕ INACTIVE"
            print(f"  • {student.full_name} ({student.student_id}) - {sessions_count} sessions {status}")
        
        print(f"\nYou can now:")
        print("1. Test the frontend at http://localhost:5173")
        print("2. Access Django admin at http://localhost:8000/admin")
        print("3. Use any of the sample Student IDs to test the system")
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
