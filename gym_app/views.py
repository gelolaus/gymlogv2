from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime, date
from .models import Student, GymSession, DailyGymStats, Feedback
from .serializers import (
    StudentRegistrationSerializer, StudentSerializer, GymSessionSerializer,
    StudentLoginSerializer, StudentRFIDLoginSerializer, CheckInOutSerializer, 
    StudentStatsSerializer, HeatmapDataSerializer, FeedbackSerializer
)
from .pdf_utils import PDFReportGenerator
from django.conf import settings
import json
from pathlib import Path


class StudentRegistrationView(APIView):
    """
    API endpoint for student registration.
    POST: Register a new student
    """
    
    def post(self, request):
        """Register a new student"""
        serializer = StudentRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            student = serializer.save()
            response_data = StudentSerializer(student).data
            return Response({
                'success': True,
                'message': 'Student registered successfully!',
                'data': response_data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Registration failed. Please check your information.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentLoginView(APIView):
    """
    API endpoint for student login using RFID.
    POST: Login with RFID
    """
    
    def post(self, request):
        """Login student using RFID"""
        serializer = StudentRFIDLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            rfid = serializer.validated_data['rfid']
            student = get_object_or_404(Student, rfid=rfid, is_active=True)
            
            # Check if student has an active session
            active_session = GymSession.objects.filter(
                student=student,
                is_active=True
            ).first()
            
            # Get daily gym time
            daily_minutes = GymSession.get_daily_gym_time(student)
            can_check_in, remaining_minutes = GymSession.can_check_in(student)
            
            # RFID Tap Logic: Auto check-in/check-out
            checked_out_session = None
            if active_session:
                # Student has active session - CHECK OUT
                active_session.check_out_time = timezone.now()
                active_session.save()
                
                # Store the completed session data before it becomes inactive
                checked_out_session = active_session
                
                # Update daily stats
                DailyGymStats.update_daily_stats(student, active_session.date)
                
                message = f'Checked out successfully! Session duration: {active_session.session_duration_formatted}'
                session_action = 'check_out'
            else:
                # Student has no active session - CHECK IN
                if not can_check_in:
                    return Response({
                        'success': False,
                        'message': 'Daily gym time limit reached (2 hours maximum)',
                        'errors': {'daily_limit': 'You have reached your 2-hour daily limit'}
                    }, status=status.HTTP_400_BAD_REQUEST)
                # Create new session
                new_session = GymSession.objects.create(
                    student=student,
                    check_in_time=timezone.now(),
                    date=timezone.now().date()
                )
                active_session = new_session
                message = f'Welcome, {student.full_name}! Checked in successfully.'
                session_action = 'check_in'
            
            # Refresh data after check-in/check-out
            active_session = GymSession.objects.filter(
                student=student,
                is_active=True
            ).first()
            daily_minutes = GymSession.get_daily_gym_time(student)
            can_check_in, remaining_minutes = GymSession.can_check_in(student)
            
            response_data = {
                'student': StudentSerializer(student).data,
                'has_active_session': active_session is not None,
                'active_session': GymSessionSerializer(active_session).data if active_session else None,
                'daily_gym_minutes': daily_minutes,
                'remaining_daily_minutes': remaining_minutes,
                'can_check_in': can_check_in,
                'action_taken': session_action,
                'completed_session': GymSessionSerializer(checked_out_session).data if checked_out_session else None
            }
            
            return Response({
                'success': True,
                'message': message,
                'data': response_data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'RFID not recognized. Please check your RFID or register first.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentIDLoginView(APIView):
    """
    API endpoint for student login using Student ID (legacy support).
    POST: Login with student ID
    """
    
    def post(self, request):
        """Login student using student ID"""
        serializer = StudentLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            student_id = serializer.validated_data['student_id']
            student = get_object_or_404(Student, student_id=student_id, is_active=True)
            
            # Check if student has an active session
            active_session = GymSession.objects.filter(
                student=student,
                is_active=True
            ).first()
            
            # Get daily gym time
            daily_minutes = GymSession.get_daily_gym_time(student)
            can_check_in, remaining_minutes = GymSession.can_check_in(student)
            
            response_data = {
                'student': StudentSerializer(student).data,
                'has_active_session': active_session is not None,
                'active_session': GymSessionSerializer(active_session).data if active_session else None,
                'daily_gym_minutes': daily_minutes,
                'remaining_daily_minutes': remaining_minutes,
                'can_check_in': can_check_in
            }
            
            return Response({
                'success': True,
                'message': f'Welcome, {student.full_name}!',
                'data': response_data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Login failed. Please check your student ID.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GymCheckInOutView(APIView):
    """
    API endpoint for gym check-in and check-out operations.
    POST: Handle check-in/check-out based on action parameter
    """
    
    def post(self, request):
        """Handle gym check-in and check-out"""
        serializer = CheckInOutSerializer(data=request.data)
        
        if serializer.is_valid():
            student = serializer.validated_data['student']
            action = serializer.validated_data['action']
            active_session = serializer.validated_data.get('active_session')
            
            try:
                with transaction.atomic():
                    if action == 'check_in':
                        # Create new gym session
                        now = timezone.now()
                        session = GymSession.objects.create(
                            student=student,
                            check_in_time=now,
                            date=now.date()
                        )
                        
                        serialized = GymSessionSerializer(session).data
                        return Response({
                            'success': True,
                            'message': f'Check-in successful! Gym timer started for {student.full_name}.',
                            'data': {
                                'session': serialized,
                                'check_in_time_iso': serialized.get('check_in_time_iso'),
                                'action': 'checked_in'
                            }
                        }, status=status.HTTP_201_CREATED)
                    
                    elif action == 'check_out':
                        # Complete the active session
                        active_session.check_out_time = timezone.now()
                        active_session.save()  # This will automatically calculate duration and set is_active=False
                        
                        # Update daily stats
                        DailyGymStats.update_daily_stats(student, active_session.date)
                        
                        # Get daily and total gym time for logout display
                        daily_minutes = GymSession.get_daily_gym_time(student, active_session.date)
                        total_minutes = student.total_gym_time_minutes
                        
                        # Format time displays
                        daily_hours = daily_minutes // 60
                        daily_mins = daily_minutes % 60
                        daily_formatted = f"{daily_hours:02d}:{daily_mins:02d}"
                        
                        total_hours = total_minutes // 60
                        total_mins = total_minutes % 60
                        total_formatted = f"{total_hours:02d}:{total_mins:02d}"
                        
                        serialized = GymSessionSerializer(active_session).data
                        return Response({
                            'success': True,
                            'message': f'Check-out successful! {student.full_name} spent {active_session.session_duration_formatted} in the gym.',
                            'data': {
                                'session': serialized,
                                'check_out_time_iso': serialized.get('check_out_time_iso'),
                                'duration_formatted': active_session.session_duration_formatted,
                                'daily_time_minutes': daily_minutes,
                                'daily_time_formatted': daily_formatted,
                                'total_time_minutes': total_minutes, 
                                'total_time_formatted': total_formatted,
                                'action': 'checked_out'
                            }
                        }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'An error occurred: {str(e)}',
                    'errors': {}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Invalid request. Please check your information.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentStatsView(APIView):
    """
    API endpoint for student statistics and heatmap data.
    GET: Get comprehensive stats for a student by student ID (legacy)
    """
    
    def get(self, request, student_id):
        """Get comprehensive statistics for a student by student ID"""
        try:
            student = get_object_or_404(Student, student_id=student_id, is_active=True)
            stats_data = StudentStatsSerializer.get_student_stats(student)
            
            return Response({
                'success': True,
                'message': f'Statistics retrieved for {student.full_name}',
                'data': stats_data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving statistics: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentRFIDStatsView(APIView):
    """
    API endpoint for student statistics using RFID authentication.
    POST: Get comprehensive stats for a student by RFID
    """
    
    def post(self, request):
        """Get comprehensive statistics for a student using RFID"""
        print(f"DEBUG: RFID Stats request data: {request.data}")
        serializer = StudentRFIDLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            rfid = serializer.validated_data['rfid']
            print(f"DEBUG: Looking up RFID: {rfid}")
            student = get_object_or_404(Student, rfid=rfid, is_active=True)
            print(f"DEBUG: Found student: {student.full_name}")
            
            try:
                print(f"DEBUG: Getting stats for student: {student.student_id}")
                stats_data = StudentStatsSerializer.get_student_stats(student)
                print(f"DEBUG: Stats data generated successfully")
                
                return Response({
                    'success': True,
                    'message': f'Statistics retrieved for {student.full_name}',
                    'data': stats_data
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                print(f"DEBUG: Error in stats generation: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'success': False,
                    'message': f'Error retrieving statistics: {str(e)}',
                    'errors': {}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        print(f"DEBUG: Serializer errors: {serializer.errors}")
        return Response({
            'success': False,
            'message': 'RFID not recognized. Please check your RFID or register first.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def check_student_status(request, student_id):
    """
    Quick endpoint to check if a student is registered and their current status.
    """
    try:
        student = Student.objects.filter(student_id=student_id, is_active=True).first()
        
        if not student:
            return Response({
                'success': False,
                'message': 'Student not found or account is inactive',
                'data': {
                    'is_registered': False,
                    'needs_registration': True
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        active_session = GymSession.objects.filter(student=student, is_active=True).first()
        daily_minutes = GymSession.get_daily_gym_time(student)
        can_check_in, remaining_minutes = GymSession.can_check_in(student)
        
        return Response({
            'success': True,
            'message': 'Student status retrieved successfully',
            'data': {
                'is_registered': True,
                'needs_registration': False,
                'student': StudentSerializer(student).data,
                'has_active_session': active_session is not None,
                'daily_gym_minutes': daily_minutes,
                'remaining_daily_minutes': remaining_minutes,
                'can_check_in': can_check_in
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error checking student status: {str(e)}',
            'errors': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PDFExportView(APIView):
    """
    API endpoint for generating PDF reports.
    Supports export by user, day, or block/section.
    """
    
    def __init__(self):
        super().__init__()
        self.pdf_generator = PDFReportGenerator()
    
    def parse_date(self, date_string):
        """Parse date string in YYYY-MM-DD format"""
        if not date_string:
            return None
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    def get(self, request):
        """Generate PDF based on query parameters"""
        export_type = request.GET.get('type')  # 'user', 'day', 'block'
        
        if export_type == 'user':
            return self.export_user_report(request)
        elif export_type == 'day':
            return self.export_daily_report(request)
        elif export_type == 'block':
            return self.export_block_report(request)
        else:
            return Response({
                'success': False,
                'message': 'Invalid export type. Use: user, day, or block',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def export_user_report(self, request):
        """Export individual user report"""
        student_id = request.GET.get('student_id')
        date_from = self.parse_date(request.GET.get('date_from'))
        date_to = self.parse_date(request.GET.get('date_to'))
        
        if not student_id:
            return Response({
                'success': False,
                'message': 'student_id parameter is required for user export',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if student exists
            student = Student.objects.get(student_id=student_id, is_active=True)
            
            # Generate PDF
            pdf_buffer = self.pdf_generator.generate_user_report(
                student_id=student_id,
                date_from=date_from,
                date_to=date_to
            )
            
            if pdf_buffer is None:
                return Response({
                    'success': False,
                    'message': 'Student not found',
                    'errors': {}
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create HTTP response
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"gym_report_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Student not found',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error generating PDF: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def export_daily_report(self, request):
        """Export daily activity report"""
        target_date_str = request.GET.get('date')
        
        if not target_date_str:
            return Response({
                'success': False,
                'message': 'date parameter is required for daily export (format: YYYY-MM-DD)',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        target_date = self.parse_date(target_date_str)
        if target_date is None:
            return Response({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generate PDF
            pdf_buffer = self.pdf_generator.generate_daily_report(target_date)
            
            # Create HTTP response
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"daily_gym_report_{target_date.strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error generating PDF: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def export_block_report(self, request):
        """Export block/section report"""
        block_section = request.GET.get('block')
        date_from = self.parse_date(request.GET.get('date_from'))
        date_to = self.parse_date(request.GET.get('date_to'))
        
        if not block_section:
            return Response({
                'success': False,
                'message': 'block parameter is required for block export',
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generate PDF
            pdf_buffer = self.pdf_generator.generate_block_report(
                block_section=block_section,
                date_from=date_from,
                date_to=date_to
            )
            
            if pdf_buffer is None:
                return Response({
                    'success': False,
                    'message': f'No students found for block/section: {block_section}',
                    'errors': {}
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create HTTP response
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"block_report_{block_section}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error generating PDF: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_available_blocks(request):
    """
    Get list of all available blocks/sections for PDF export filtering.
    """
    try:
        blocks = Student.objects.filter(is_active=True).values_list('block_section', flat=True).distinct().order_by('block_section')
        
        return Response({
            'success': True,
            'message': 'Available blocks retrieved successfully',
            'data': {
                'blocks': list(blocks)
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving blocks: {str(e)}',
            'errors': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedbackView(APIView):
    """
    Accept user feedback and log to a JSONL file on the server.
    """
    def post(self, request):
        try:
            payload = {
                'full_name': request.data.get('full_name', '').strip(),
                'block_section': request.data.get('block_section', '').strip(),
                'email': request.data.get('email', '').strip(),
                'message': request.data.get('message', '').strip(),
                'submitted_at': timezone.now().isoformat()
            }

            if not payload['full_name'] or not payload['email'] or not payload['message']:
                return Response({
                    'success': False,
                    'message': 'Full Name, Email, and Message are required.',
                    'errors': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Enforce APC student email domain
            email_lower = payload['email'].lower()
            if not email_lower.endswith('@student.apc.edu.ph'):
                return Response({
                    'success': False,
                    'message': 'Please use your APC student email (ends with @student.apc.edu.ph).',
                    'errors': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            feedback_dir = Path(settings.BASE_DIR) / 'OLD_LOGS'
            feedback_dir.mkdir(exist_ok=True)
            feedback_file = feedback_dir / 'feedback.jsonl'

            # Persist to DB
            feedback = Feedback.objects.create(
                full_name=payload['full_name'],
                block_section=payload['block_section'] or '',
                email=payload['email'],
                message=payload['message'],
                source_ip=request.META.get('REMOTE_ADDR')
            )

            # Also append to file for redundancy
            with open(feedback_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(FeedbackSerializer(feedback).data, ensure_ascii=False) + '\n')

            return Response({
                'success': True,
                'message': 'Thank you! Your feedback has been submitted.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error submitting feedback: {str(e)}',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedbackListView(generics.ListAPIView):
    queryset = Feedback.objects.all().order_by('-submitted_at')
    serializer_class = FeedbackSerializer