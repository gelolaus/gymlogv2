"""
Django management command to import old gym data from JSON files.
Usage: python manage.py import_old_data
"""

import json
import os
import re
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from gym_app.models import Student, GymSession, DailyGymStats
from django.db import transaction


class Command(BaseCommand):
    help = 'Import old gym data from JSON files in OLD_LOGS directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Import specific file only (e.g., 08-05-2025.json)',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.specific_file = options['file']
        
        # Define the OLD_LOGS directory path
        old_logs_dir = os.path.join(os.getcwd(), 'OLD_LOGS')
        
        if not os.path.exists(old_logs_dir):
            raise CommandError('OLD_LOGS directory not found')
        
        # Define the file mapping for dates
        file_date_mapping = {
            '08-04-2025.json': date(2025, 8, 4),
            '08-05-2025.json': date(2025, 8, 5),
            '08-07-2025.json': date(2025, 8, 7),
            '08-08-2025.json': date(2025, 8, 8),
            '08-11-2025.json': date(2025, 8, 11),
            '08-12-2025.json': date(2025, 8, 12),
            '08-14-2025.json': date(2025, 8, 14),
            '08-15-2025.json': date(2025, 8, 15),
            '08-18-2025.json': date(2025, 8, 18),
            '08-19-2025.json': date(2025, 8, 19),
        }
        
        # Filter files if specific file requested
        if self.specific_file:
            if self.specific_file not in file_date_mapping:
                raise CommandError(f'File {self.specific_file} not found in mapping')
            file_date_mapping = {self.specific_file: file_date_mapping[self.specific_file]}
        
        total_sessions = 0
        total_students = 0
        
        for filename, session_date in file_date_mapping.items():
            file_path = os.path.join(old_logs_dir, filename)
            
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f'File {filename} not found, skipping...')
                )
                continue
            
            self.stdout.write(f'Processing {filename} for date {session_date}...')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sessions_count, students_count = self.process_file_data(data, session_date)
                total_sessions += sessions_count
                total_students += students_count
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {filename}: {sessions_count} sessions, {students_count} students'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {filename}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Import completed! Total: {total_sessions} sessions, {total_students} students'
            )
        )
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no data was actually imported.')
            )

    def process_file_data(self, data, session_date):
        """Process data from a single JSON file"""
        sessions_created = 0
        students_created = 0
        
        with transaction.atomic():
            for entry in data:
                try:
                    # Parse student data
                    student_data = self.parse_student_data(entry)
                    
                    # Create or get student
                    student, created = self.get_or_create_student(student_data)
                    if created:
                        students_created += 1
                    
                    # Parse session data
                    session_data = self.parse_session_data(entry, session_date)
                    
                    # Create gym session
                    if not self.dry_run:
                        session = self.create_gym_session(student, session_data)
                        if session:
                            sessions_created += 1
                    else:
                        sessions_created += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Skipping entry: {str(e)}')
                    )
                    continue
        
        return sessions_created, students_created

    def parse_student_data(self, entry):
        """Parse and clean student data from JSON entry"""
        full_name = entry.get('full_name', '').strip()
        raw_student_id = entry.get('student_id', '').strip()
        enrolled_block = entry.get('enrolled_block', '').strip()
        pe_course = entry.get('pe_course', '').strip().lower()
        
        # Parse name (last word is last name, rest is first name)
        name_parts = full_name.split()
        if len(name_parts) < 2:
            raise ValueError(f'Invalid name format: {full_name}')
        
        last_name = name_parts[-1]
        first_name = ' '.join(name_parts[:-1])
        
        # Clean and validate student ID
        student_id = self.clean_student_id(raw_student_id)
        
        # Map PE course
        pe_course_mapping = {
            'pedu1': 'PEDUONE',
            'pedu2': 'PEDUTWO', 
            'pedu3': 'PEDUTRI',
            'pedu4': 'PEDUFOR',
            'none': 'N/A',
        }
        pe_course_clean = pe_course_mapping.get(pe_course, 'N/A')
        
        # Clean block section
        block_section = enrolled_block.replace(' ', '').replace('-', '') if enrolled_block else 'N/A'
        if not block_section or block_section.upper() == 'NONE':
            block_section = 'N/A'
        
        return {
            'student_id': student_id,
            'first_name': first_name,
            'last_name': last_name,
            'pe_course': pe_course_clean,
            'block_section': block_section,
        }

    def clean_student_id(self, raw_id):
        """Clean and validate student ID to match 20xx-xxxxxx format"""
        # Remove extra spaces and characters
        clean_id = re.sub(r'[^\d-]', '', raw_id)
        
        # Check if it already matches the pattern
        if re.match(r'^20\d{2}-\d{6}$', clean_id):
            return clean_id
        
        # Try to extract a valid pattern
        # Look for 20xx followed by 6 digits
        match = re.search(r'(20\d{2}).*?(\d{6})', raw_id)
        if match:
            year, number = match.groups()
            return f'{year}-{number}'
        
        # If we can't fix it, generate a placeholder ID
        # Use the original as a base but ensure uniqueness
        timestamp = str(int(datetime.now().timestamp()))[-6:]
        return f'2024-{timestamp}'

    def parse_session_data(self, entry, session_date):
        """Parse session timing data"""
        workout_start = entry.get('workout_start', '')
        workout_end = entry.get('workout_end', '')
        
        # Parse time strings (format: HH:MM:SS)
        try:
            start_time = datetime.strptime(workout_start, '%H:%M:%S').time()
            end_time = datetime.strptime(workout_end, '%H:%M:%S').time()
        except ValueError:
            raise ValueError(f'Invalid time format: start={workout_start}, end={workout_end}')
        
        # Create datetime objects for the session date
        start_datetime = datetime.combine(session_date, start_time)
        end_datetime = datetime.combine(session_date, end_time)
        
        # Handle case where end time is next day (rare but possible)
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
        
        # Calculate duration in minutes
        duration = (end_datetime - start_datetime).total_seconds() / 60
        
        return {
            'check_in_time': timezone.make_aware(start_datetime),
            'check_out_time': timezone.make_aware(end_datetime),
            'duration_minutes': int(duration),
            'date': session_date,
        }

    def get_or_create_student(self, student_data):
        """Get existing student or create new one"""
        if self.dry_run:
            # For dry run, just check if student exists
            exists = Student.objects.filter(student_id=student_data['student_id']).exists()
            return None, not exists
        
        student, created = Student.objects.get_or_create(
            student_id=student_data['student_id'],
            defaults={
                'first_name': student_data['first_name'],
                'last_name': student_data['last_name'],
                'pe_course': student_data['pe_course'],
                'block_section': student_data['block_section'],
            }
        )
        
        # Update fields if student exists but data is different
        if not created:
            updated = False
            if student.first_name != student_data['first_name']:
                student.first_name = student_data['first_name']
                updated = True
            if student.last_name != student_data['last_name']:
                student.last_name = student_data['last_name']
                updated = True
            if student.pe_course != student_data['pe_course'] and student_data['pe_course'] != 'N/A':
                student.pe_course = student_data['pe_course']
                updated = True
            if student.block_section != student_data['block_section'] and student_data['block_section'] != 'N/A':
                student.block_section = student_data['block_section']
                updated = True
            
            if updated:
                student.save()
        
        return student, created

    def create_gym_session(self, student, session_data):
        """Create a gym session"""
        # Check if session already exists
        existing_session = GymSession.objects.filter(
            student=student,
            date=session_data['date'],
            check_in_time=session_data['check_in_time'],
        ).first()
        
        if existing_session:
            return None  # Skip duplicate
        
        session = GymSession.objects.create(
            student=student,
            check_in_time=session_data['check_in_time'],
            check_out_time=session_data['check_out_time'],
            duration_minutes=session_data['duration_minutes'],
            date=session_data['date'],
            is_active=False,  # All old sessions are completed
        )
        
        # Update daily stats
        DailyGymStats.update_daily_stats(student, session_data['date'])
        
        return session
