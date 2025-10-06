from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import re


class Student(models.Model):
    """
    Model to store student information for gym registration.
    
    Fields:
    - student_id: Unique student ID with format "20xx-xxxxxx"
    - first_name: Student's first name
    - last_name: Student's last name
    - pe_course: PE course enrollment (PEDUONE, PEDUTWO, PEDUTRI, PEDUFOR, or N/A)
    - block_section: Student's block/section (no spaces allowed)
    - rfid: RFID tag identifier for gym access
    - registration_date: When the student first registered
    - is_active: Whether the student account is active
    """
    
    PE_COURSE_CHOICES = [
        ('PEDUONE', 'PEDU ONE'),
        ('PEDUTWO', 'PEDU TWO'),
        ('PEDUTRI', 'PEDU TRI'),
        ('PEDUFOR', 'PEDU FOR'),
        ('N/A', 'Not Enrolled in PE'),
    ]
    
    # Validator for student ID format: 20xx-xxxxxx
    student_id_validator = RegexValidator(
        regex=r'^20\d{2}-\d{6}$',
        message='Student ID must be in format 20xx-xxxxxx (e.g., 2023-123456)'
    )
    
    student_id = models.CharField(
        max_length=11,
        unique=True,
        validators=[student_id_validator],
        help_text='Format: 20xx-xxxxxx'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pe_course = models.CharField(
        max_length=10,
        choices=PE_COURSE_CHOICES,
        default='N/A'
    )
    block_section = models.CharField(
        max_length=20,
        help_text='Block/Section (no spaces allowed, e.g., STEM241, CS231)'
    )
    rfid = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text='RFID tag identifier for gym access'
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'gym_students'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.student_id} - {self.last_name}, {self.first_name}"
    
    def clean(self):
        """Custom validation to remove spaces from block_section"""
        if self.block_section:
            self.block_section = re.sub(r'\s+', '', self.block_section.upper())
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_gym_sessions(self):
        """Returns the total number of completed gym sessions"""
        return self.gym_sessions.filter(check_out_time__isnull=False).count()
    
    @property
    def total_gym_time_minutes(self):
        """Returns total gym time in minutes across all sessions"""
        sessions = self.gym_sessions.filter(check_out_time__isnull=False)
        total_minutes = 0
        for session in sessions:
            duration = session.check_out_time - session.check_in_time
            total_minutes += duration.total_seconds() / 60
        return int(total_minutes)


class GymSession(models.Model):
    """
    Model to track individual gym sessions for each student.
    
    Fields:
    - student: Foreign key to Student model
    - check_in_time: When the student checked in
    - check_out_time: When the student checked out (null if still active)
    - duration_minutes: Calculated duration of the session
    - date: Date of the session (for easier querying)
    - is_active: Whether this is an active session
    """
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='gym_sessions'
    )
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'gym_sessions'
        ordering = ['-check_in_time']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        status = "Active" if self.is_active else "Completed"
        return f"{self.student.student_id} - {self.date} ({status})"
    
    def save(self, *args, **kwargs):
        """Calculate duration when session is completed"""
        if self.check_out_time and self.check_in_time:
            duration = self.check_out_time - self.check_in_time
            self.duration_minutes = int(duration.total_seconds() / 60)
            self.is_active = False
        super().save(*args, **kwargs)
    
    @property
    def session_duration_formatted(self):
        """Returns duration in HH:MM format"""
        if self.duration_minutes:
            hours = self.duration_minutes // 60
            minutes = self.duration_minutes % 60
            return f"{hours:02d}:{minutes:02d}"
        return "00:00"
    
    @classmethod
    def get_daily_gym_time(cls, student, date=None):
        """
        Returns total gym time for a student on a specific date.
        If no date is provided, uses today's date.
        """
        if date is None:
            date = timezone.now().date()
        
        sessions = cls.objects.filter(
            student=student,
            date=date,
            check_out_time__isnull=False
        )
        
        total_minutes = sum(session.duration_minutes for session in sessions)
        return total_minutes
    
    @classmethod
    def can_check_in(cls, student, date=None):
        """
        Checks if student can check in based on 2-hour daily limit.
        Returns (can_check_in: bool, remaining_minutes: int)
        """
        if date is None:
            date = timezone.now().date()
        
        # Check if student has an active session
        active_session = cls.objects.filter(
            student=student,
            is_active=True
        ).first()
        
        if active_session:
            return False, 0  # Already has active session
        
        daily_minutes = cls.get_daily_gym_time(student, date)
        max_daily_minutes = 120  # 2 hours
        remaining_minutes = max_daily_minutes - daily_minutes
        
        return remaining_minutes > 0, max(0, remaining_minutes)


class DailyGymStats(models.Model):
    """
    Model to store aggregated daily gym statistics for performance optimization.
    This will help with generating heatmaps efficiently.
    """
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )
    date = models.DateField()
    total_sessions = models.PositiveIntegerField(default=0)
    total_minutes = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'gym_daily_stats'
        unique_together = ['student', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['student', 'date']),
        ]
    
    def __str__(self):
        return f"{self.student.student_id} - {self.date} ({self.total_minutes}min)"
    
    @classmethod
    def update_daily_stats(cls, student, date):
        """
        Updates or creates daily stats for a student on a specific date.
        This should be called after each gym session completion.
        """
        sessions = GymSession.objects.filter(
            student=student,
            date=date,
            check_out_time__isnull=False
        )
        
        total_sessions = sessions.count()
        total_minutes = sum(session.duration_minutes for session in sessions)
        
        stats, created = cls.objects.update_or_create(
            student=student,
            date=date,
            defaults={
                'total_sessions': total_sessions,
                'total_minutes': total_minutes
            }
        )
        
        return stats


class Feedback(models.Model):
    """
    Store user feedback submissions.
    """
    full_name = models.CharField(max_length=150)
    block_section = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    source_ip = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = 'gym_feedbacks'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}> @ {self.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}"