from rest_framework import serializers
from .models import Student, GymSession, DailyGymStats, Feedback
from django.utils import timezone
from datetime import datetime, timedelta
import re


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for student registration.
    Includes validation for student ID format and block section formatting.
    """
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 
            'pe_course', 'block_section', 'rfid'
        ]
    
    def validate_student_id(self, value):
        """Validate student ID format"""
        if not re.match(r'^20\d{2}-\d{6}$', value):
            raise serializers.ValidationError(
                "Student ID must be in format 20xx-xxxxxx (e.g., 2023-123456)"
            )
        return value
    
    def validate_block_section(self, value):
        """Remove spaces and convert to uppercase"""
        if value:
            return re.sub(r'\s+', '', value.upper())
        return value
    
    def validate_rfid(self, value):
        """Validate RFID field"""
        if not value or not value.strip():
            raise serializers.ValidationError("RFID is required for registration.")
        
        # Check if RFID already exists
        if Student.objects.filter(rfid=value.strip()).exists():
            raise serializers.ValidationError("This RFID is already registered to another student.")
        
        return value.strip()
    
    def validate(self, data):
        """Additional validation"""
        # Check if student ID already exists
        if Student.objects.filter(student_id=data['student_id']).exists():
            raise serializers.ValidationError({
                'student_id': 'A student with this ID is already registered.'
            })
        return data


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for student data including computed fields.
    """
    full_name = serializers.ReadOnlyField()
    total_gym_sessions = serializers.ReadOnlyField()
    total_gym_time_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'first_name', 'last_name', 'full_name',
            'pe_course', 'block_section', 'rfid', 'registration_date', 'is_active',
            'total_gym_sessions', 'total_gym_time_minutes'
        ]
        read_only_fields = ['id', 'registration_date']


class GymSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for gym sessions.
    """
    student_info = StudentSerializer(source='student', read_only=True)
    session_duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = GymSession
        fields = [
            'id', 'student', 'student_info', 'check_in_time', 'check_out_time',
            'duration_minutes', 'session_duration_formatted', 'date', 'is_active'
        ]
        read_only_fields = ['id', 'check_in_time', 'duration_minutes', 'date']


class StudentLoginSerializer(serializers.Serializer):
    """
    Serializer for student login (temporary implementation using student ID).
    """
    student_id = serializers.CharField(max_length=11)
    
    def validate_student_id(self, value):
        """Validate that student exists and is active"""
        try:
            student = Student.objects.get(student_id=value, is_active=True)
        except Student.DoesNotExist:
            raise serializers.ValidationError(
                "Student not found or account is inactive. Please register first."
            )
        return value


class StudentRFIDLoginSerializer(serializers.Serializer):
    """
    Serializer for student login using RFID.
    """
    rfid = serializers.CharField(max_length=50)
    
    def validate_rfid(self, value):
        """Validate that student exists and is active"""
        try:
            student = Student.objects.get(rfid=value.strip(), is_active=True)
        except Student.DoesNotExist:
            raise serializers.ValidationError(
                "RFID not recognized or account is inactive. Please check your RFID or register first."
            )
        return value.strip()


class CheckInOutSerializer(serializers.Serializer):
    """
    Serializer for gym check-in and check-out operations.
    """
    student_id = serializers.CharField(max_length=11)
    action = serializers.ChoiceField(choices=['check_in', 'check_out'])
    
    def validate(self, data):
        """Validate check-in/check-out operations"""
        student_id = data['student_id']
        action = data['action']
        
        try:
            student = Student.objects.get(student_id=student_id, is_active=True)
        except Student.DoesNotExist:
            raise serializers.ValidationError({
                'student_id': 'Student not found or account is inactive.'
            })
        
        # Check for active session
        active_session = GymSession.objects.filter(
            student=student,
            is_active=True
        ).first()
        
        if action == 'check_in':
            if active_session:
                raise serializers.ValidationError({
                    'action': 'Student is already checked in. Please check out first.'
                })
            
            # Check daily time limit
            can_check_in, remaining_minutes = GymSession.can_check_in(student)
            if not can_check_in:
                raise serializers.ValidationError({
                    'action': f'Daily gym time limit reached (2 hours maximum). '
                             f'Remaining time: {remaining_minutes} minutes.'
                })
        
        elif action == 'check_out':
            if not active_session:
                raise serializers.ValidationError({
                    'action': 'Student is not currently checked in.'
                })
        
        data['student'] = student
        data['active_session'] = active_session
        return data


class DailyStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for daily gym statistics.
    """
    
    class Meta:
        model = DailyGymStats
        fields = ['date', 'total_sessions', 'total_minutes']


class HeatmapDataSerializer(serializers.Serializer):
    """
    Serializer for heatmap data (GitHub-style).
    Returns data in format suitable for frontend heatmap visualization.
    """
    date = serializers.DateField()
    count = serializers.IntegerField()
    level = serializers.IntegerField()  # 0-4 intensity level
    
    @staticmethod
    def generate_heatmap_data(student, start_date=None, end_date=None):
        """
        Generate heatmap data for a student.
        Returns list of {date, count, level} for each day in the range.
        Only includes workdays (Monday-Friday) with proper intensity levels.
        """
        if end_date is None:
            end_date = timezone.now().date()
        if start_date is None:
            start_date = end_date - timedelta(days=365)  # Last year
        
        # Get all daily stats for the student in the date range
        stats = DailyGymStats.objects.filter(
            student=student,
            date__range=[start_date, end_date]
        ).values('date', 'total_minutes')
        
        # Create a dictionary for quick lookup
        stats_dict = {stat['date']: stat['total_minutes'] for stat in stats}
        
        # Determine intensity levels based on minutes
        # Level 0: 0 minutes, Level 1: 1-30min, Level 2: 31-60min, 
        # Level 3: 61-90min, Level 4: 91+ minutes
        def get_intensity_level(minutes):
            if minutes == 0:
                return 0
            elif minutes <= 30:
                return 1
            elif minutes <= 60:
                return 2
            elif minutes <= 90:
                return 3
            else:
                return 4
        
        # Generate data for each workday in the range (Monday-Friday)
        heatmap_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Only include workdays (Monday=0, Friday=4)
            if current_date.weekday() < 5:  # Monday to Friday
                minutes = stats_dict.get(current_date, 0)
                heatmap_data.append({
                    'date': current_date,
                    'count': minutes,
                    'level': get_intensity_level(minutes)
                })
            current_date += timedelta(days=1)
        
        return heatmap_data


class StudentStatsSerializer(serializers.Serializer):
    """
    Comprehensive serializer for student statistics.
    """
    student_info = StudentSerializer(read_only=True)
    heatmap_data = serializers.ListField(child=HeatmapDataSerializer(), read_only=True)
    total_days_active = serializers.IntegerField(read_only=True)
    average_session_duration = serializers.IntegerField(read_only=True)
    longest_session_minutes = serializers.IntegerField(read_only=True)
    current_streak = serializers.IntegerField(read_only=True)
    longest_streak = serializers.IntegerField(read_only=True)
    
    @staticmethod
    def get_student_stats(student):
        """
        Calculate comprehensive statistics for a student.
        """
        # Get all completed sessions
        sessions = GymSession.objects.filter(
            student=student,
            check_out_time__isnull=False
        ).order_by('date')
        
        if not sessions.exists():
            return {
                'student_info': StudentSerializer(student).data,
                'heatmap_data': HeatmapDataSerializer.generate_heatmap_data(student),
                'total_days_active': 0,
                'average_session_duration': 0,
                'longest_session_minutes': 0,
                'current_streak': 0,
                'longest_streak': 0
            }
        
        # Calculate statistics
        total_days_active = sessions.values('date').distinct().count()
        from django.db.models import Avg, Max
        average_duration = sessions.aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0
        longest_session = sessions.aggregate(
            max=Max('duration_minutes')
        )['max'] or 0
        
        # Calculate streaks (consecutive days with gym activity)
        daily_stats = DailyGymStats.objects.filter(
            student=student,
            total_minutes__gt=0
        ).order_by('date')
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        if daily_stats.exists():
            dates = [stat.date for stat in daily_stats]
            today = timezone.now().date()
            
            # Calculate current streak
            for i in range(len(dates) - 1, -1, -1):
                if dates[i] == today - timedelta(days=len(dates) - 1 - i):
                    current_streak += 1
                else:
                    break
            
            # Calculate longest streak
            for i in range(len(dates)):
                if i == 0 or dates[i] == dates[i-1] + timedelta(days=1):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
        
        return {
            'student_info': StudentSerializer(student).data,
            'heatmap_data': HeatmapDataSerializer.generate_heatmap_data(student),
            'total_days_active': total_days_active,
            'average_session_duration': int(round(average_duration)),
            'longest_session_minutes': longest_session,
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'full_name', 'block_section', 'email', 'message', 'submitted_at']
        read_only_fields = ['id', 'submitted_at']
