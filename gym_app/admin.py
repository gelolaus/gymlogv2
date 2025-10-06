from django.contrib import admin
from .models import Student, GymSession, DailyGymStats, Feedback


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Admin interface for Student model.
    Provides comprehensive management of student records.
    """
    list_display = [
        'student_id', 'last_name', 'first_name', 'rfid', 'pe_course', 
        'block_section', 'total_gym_sessions', 'registration_date', 'is_active'
    ]
    list_filter = ['pe_course', 'is_active', 'registration_date', 'block_section']
    search_fields = ['student_id', 'first_name', 'last_name', 'block_section', 'rfid']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['registration_date', 'total_gym_sessions', 'total_gym_time_minutes']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_id', 'first_name', 'last_name')
        }),
        ('RFID Access', {
            'fields': ('rfid',)
        }),
        ('Academic Information', {
            'fields': ('pe_course', 'block_section')
        }),
        ('Account Status', {
            'fields': ('is_active', 'registration_date')
        }),
        ('Gym Statistics', {
            'fields': ('total_gym_sessions', 'total_gym_time_minutes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related for gym sessions"""
        return super().get_queryset(request).prefetch_related('gym_sessions')


@admin.register(GymSession)
class GymSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for GymSession model.
    Allows monitoring and management of gym sessions.
    """
    list_display = [
        'student', 'check_in_time', 'check_out_time', 
        'session_duration_formatted', 'date', 'is_active'
    ]
    list_filter = ['is_active', 'date', 'check_in_time']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    ordering = ['-check_in_time']
    readonly_fields = ['duration_minutes', 'date', 'session_duration_formatted']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('student', 'check_in_time', 'check_out_time')
        }),
        ('Session Details', {
            'fields': ('duration_minutes', 'session_duration_formatted', 'date', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for student"""
        return super().get_queryset(request).select_related('student')
    
    actions = ['mark_as_completed', 'mark_as_active']
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark sessions as completed"""
        from django.utils import timezone
        updated = 0
        for session in queryset.filter(is_active=True):
            session.check_out_time = timezone.now()
            session.save()
            updated += 1
        
        self.message_user(
            request, 
            f"Successfully marked {updated} sessions as completed."
        )
    mark_as_completed.short_description = "Mark selected sessions as completed"
    
    def mark_as_active(self, request, queryset):
        """Admin action to mark sessions as active (remove check-out time)"""
        updated = queryset.filter(is_active=False).update(
            check_out_time=None, 
            is_active=True, 
            duration_minutes=0
        )
        self.message_user(
            request, 
            f"Successfully marked {updated} sessions as active."
        )
    mark_as_active.short_description = "Mark selected sessions as active"


@admin.register(DailyGymStats)
class DailyGymStatsAdmin(admin.ModelAdmin):
    """
    Admin interface for DailyGymStats model.
    Provides insights into daily gym usage patterns.
    """
    list_display = [
        'student', 'date', 'total_sessions', 'total_minutes', 'total_hours'
    ]
    list_filter = ['date', 'total_sessions']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    ordering = ['-date', '-total_minutes']
    readonly_fields = ['total_hours']
    
    def total_hours(self, obj):
        """Calculate total hours from minutes"""
        return round(obj.total_minutes / 60, 2)
    total_hours.short_description = 'Total Hours'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for student"""
        return super().get_queryset(request).select_related('student')


# Customize admin site header and title
admin.site.site_header = "APC Gym Log System Administration"
admin.site.site_title = "APC Gym Log Admin"
admin.site.index_title = "Welcome to APC Gym Log System Administration"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'block_section', 'submitted_at')
    search_fields = ('full_name', 'email', 'block_section', 'message')
    list_filter = ('submitted_at',)