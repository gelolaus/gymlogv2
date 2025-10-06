"""
PDF generation utilities for APC Gym Log System
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.utils import ImageReader
from datetime import datetime, timedelta, date
from django.http import HttpResponse
from django.utils import timezone
from .models import Student, GymSession, DailyGymStats
import io
import base64
from django.db.models import Q, Sum


class PDFReportGenerator:
    """Generate PDF reports for gym data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    # --- Datetime formatting helpers (ensure local timezone display) ---
    def _format_datetime(self, dt, fmt: str) -> str:
        if not dt:
            return ""
        # Support both datetime and date objects
        if isinstance(dt, datetime):
            local_dt = timezone.localtime(dt)
            return local_dt.strftime(fmt)
        if isinstance(dt, date):
            # Dates are timezone-agnostic; format directly
            return dt.strftime(fmt)
        # Fallback to string cast to avoid hard failures
        try:
            return str(dt)
        except Exception:
            return ""

    def _format_date(self, dt: datetime, fmt: str = "%m/%d/%Y") -> str:
        return self._format_datetime(dt, fmt)

    def _format_time(self, dt: datetime, fmt: str = "%I:%M %p") -> str:
        return self._format_datetime(dt, fmt)
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f2937')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.HexColor('#374151')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.HexColor('#4b5563')
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280')
        ))
    
    def create_header(self, story, title, subtitle=None):
        """Create document header"""
        # Title
        story.append(Paragraph("APC Gym Log System", self.styles['CustomTitle']))
        story.append(Paragraph(title, self.styles['CustomHeading']))
        
        if subtitle:
            story.append(Paragraph(subtitle, self.styles['CustomSubHeading']))
        
        # Generation info
        generation_time = self._format_datetime(timezone.now(), "%B %d, %Y at %I:%M %p")
        story.append(Paragraph(f"Generated on: {generation_time}", self.styles['Footer']))
        story.append(Spacer(1, 20))
    
    def create_student_summary_table(self, students_data):
        """Create summary table for multiple students"""
        # Table headers
        headers = ['Student ID', 'Name', 'Block/Section', 'Total Sessions', 'Total Time', 'Last Activity']
        data = [headers]
        
        for student_data in students_data:
            last_session = student_data.get('last_session')
            last_activity = self._format_date(last_session) if last_session else "No activity"
            
            row = [
                student_data['student_id'],
                student_data['full_name'],
                student_data['block_section'],
                str(student_data['total_sessions']),
                f"{student_data['total_minutes']} min",
                last_activity
            ]
            data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows style
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        
        return table
    
    def create_session_details_table(self, sessions):
        """Create detailed session table"""
        headers = ['Date', 'Check In', 'Check Out', 'Duration', 'Status']
        data = [headers]
        
        for session in sessions:
            check_out = self._format_time(session.check_out_time) if session.check_out_time else "Active"
            status = "Completed" if session.check_out_time else "Active"
            
            row = [
                self._format_date(session.check_in_time),
                self._format_time(session.check_in_time),
                check_out,
                session.session_duration_formatted,
                status
            ]
            data.append(row)
        
        table = Table(data, repeatRows=1, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows style
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ]))
        
        return table
    
    def generate_user_report(self, student_id, date_from=None, date_to=None):
        """Generate PDF report for a specific user"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        try:
            # Get student
            student = Student.objects.get(student_id=student_id, is_active=True)
            
            # Filter sessions by date range
            sessions_query = GymSession.objects.filter(student=student)
            if date_from:
                sessions_query = sessions_query.filter(check_in_time__date__gte=date_from)
            if date_to:
                sessions_query = sessions_query.filter(check_in_time__date__lte=date_to)
            
            sessions = sessions_query.order_by('-check_in_time')
            
            # Create header
            date_range = ""
            if date_from or date_to:
                if date_from and date_to:
                    date_range = f" ({date_from.strftime('%m/%d/%Y')} - {date_to.strftime('%m/%d/%Y')})"
                elif date_from:
                    date_range = f" (From {date_from.strftime('%m/%d/%Y')})"
                elif date_to:
                    date_range = f" (Until {date_to.strftime('%m/%d/%Y')})"
            
            self.create_header(
                story, 
                f"Individual Gym Report{date_range}",
                f"Student: {student.full_name} ({student.student_id})"
            )
            
            # Student Information
            story.append(Paragraph("Student Information", self.styles['CustomHeading']))
            student_info = f"""
            <b>Student ID:</b> {student.student_id}<br/>
            <b>Name:</b> {student.full_name}<br/>
            <b>PE Course:</b> {student.get_pe_course_display()}<br/>
            <b>Block/Section:</b> {student.block_section}<br/>
            <b>Registration Date:</b> {student.registration_date.strftime('%B %d, %Y')}<br/>
            """
            story.append(Paragraph(student_info, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Statistics
            total_sessions = sessions.filter(check_out_time__isnull=False).count()
            total_minutes = sum(session.duration_minutes for session in sessions if session.duration_minutes)
            total_hours = total_minutes // 60
            remaining_minutes = total_minutes % 60
            
            story.append(Paragraph("Statistics Summary", self.styles['CustomHeading']))
            stats_info = f"""
            <b>Total Completed Sessions:</b> {total_sessions}<br/>
            <b>Total Gym Time:</b> {total_hours}h {remaining_minutes}m ({total_minutes} minutes)<br/>
            <b>Average Session Duration:</b> {total_minutes // total_sessions if total_sessions > 0 else 0} minutes<br/>
            <b>First Session:</b> {self._format_date(sessions.last().check_in_time, '%B %d, %Y') if sessions.exists() else 'No sessions'}<br/>
            <b>Latest Session:</b> {self._format_date(sessions.first().check_in_time, '%B %d, %Y') if sessions.exists() else 'No sessions'}<br/>
            """
            story.append(Paragraph(stats_info, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Session Details
            if sessions.exists():
                story.append(Paragraph("Session Details", self.styles['CustomHeading']))
                story.append(self.create_session_details_table(sessions))
            else:
                story.append(Paragraph("No sessions found for the specified criteria.", self.styles['Normal']))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph("Generated by APC Gym Log System", self.styles['Footer']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Student.DoesNotExist:
            return None
    
    def generate_daily_report(self, target_date):
        """Generate PDF report for all activity on a specific day"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        # Get all sessions for the date
        sessions = GymSession.objects.filter(date=target_date).order_by('check_in_time')
        
        # Create header
        self.create_header(
            story,
            "Daily Gym Activity Report",
            f"Date: {target_date.strftime('%A, %B %d, %Y')}"
        )
        
        # Daily statistics
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(check_out_time__isnull=False).count()
        active_sessions = sessions.filter(is_active=True).count()
        total_minutes = sum(session.duration_minutes for session in sessions if session.duration_minutes)
        unique_students = sessions.values('student').distinct().count()
        
        story.append(Paragraph("Daily Overview", self.styles['CustomHeading']))
        overview_info = f"""
        <b>Total Sessions:</b> {total_sessions}<br/>
        <b>Completed Sessions:</b> {completed_sessions}<br/>
        <b>Active Sessions:</b> {active_sessions}<br/>
        <b>Total Gym Time:</b> {total_minutes} minutes ({total_minutes // 60}h {total_minutes % 60}m)<br/>
        <b>Unique Students:</b> {unique_students}<br/>
        """
        story.append(Paragraph(overview_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        if sessions.exists():
            # Session details table
            story.append(Paragraph("Session Details", self.styles['CustomHeading']))
            
            headers = ['Student ID', 'Student Name', 'Check In', 'Check Out', 'Duration', 'Status']
            data = [headers]
            
            for session in sessions:
                check_out = self._format_time(session.check_out_time) if session.check_out_time else "Active"
                status = "Completed" if session.check_out_time else "Active"
                
                row = [
                    session.student.student_id,
                    session.student.full_name,
                    self._format_time(session.check_in_time),
                    check_out,
                    session.session_duration_formatted,
                    status
                ]
                data.append(row)
            
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows style
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')]),
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("No gym activity recorded for this date.", self.styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by APC Gym Log System", self.styles['Footer']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_block_report(self, block_section, date_from=None, date_to=None):
        """Generate PDF report for all students in a specific block/section"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        # Get students from the block
        students = Student.objects.filter(block_section__iexact=block_section, is_active=True)
        
        if not students.exists():
            return None
        
        # Create header
        date_range = ""
        if date_from or date_to:
            if date_from and date_to:
                date_range = f" ({date_from.strftime('%m/%d/%Y')} - {date_to.strftime('%m/%d/%Y')})"
            elif date_from:
                date_range = f" (From {date_from.strftime('%m/%d/%Y')})"
            elif date_to:
                date_range = f" (Until {date_to.strftime('%m/%d/%Y')})"
        
        self.create_header(
            story,
            f"Block/Section Gym Report{date_range}",
            f"Block/Section: {block_section.upper()}"
        )
        
        # Collect student data
        students_data = []
        total_block_sessions = 0
        total_block_minutes = 0
        
        for student in students:
            sessions_query = GymSession.objects.filter(student=student)
            if date_from:
                sessions_query = sessions_query.filter(check_in_time__date__gte=date_from)
            if date_to:
                sessions_query = sessions_query.filter(check_in_time__date__lte=date_to)
            
            completed_sessions = sessions_query.filter(check_out_time__isnull=False)
            total_sessions = completed_sessions.count()
            total_minutes = sum(session.duration_minutes for session in completed_sessions if session.duration_minutes)
            last_session = sessions_query.order_by('-check_in_time').first()
            
            students_data.append({
                'student_id': student.student_id,
                'full_name': student.full_name,
                'block_section': student.block_section,
                'total_sessions': total_sessions,
                'total_minutes': total_minutes,
                'last_session': last_session.check_in_time.date() if last_session else None
            })
            
            total_block_sessions += total_sessions
            total_block_minutes += total_minutes
        
        # Block overview
        story.append(Paragraph("Block Overview", self.styles['CustomHeading']))
        overview_info = f"""
        <b>Total Students:</b> {len(students_data)}<br/>
        <b>Total Sessions:</b> {total_block_sessions}<br/>
        <b>Total Gym Time:</b> {total_block_minutes} minutes ({total_block_minutes // 60}h {total_block_minutes % 60}m)<br/>
        <b>Average Sessions per Student:</b> {total_block_sessions / len(students_data) if students_data else 0:.1f}<br/>
        <b>Average Time per Student:</b> {total_block_minutes / len(students_data) if students_data else 0:.0f} minutes<br/>
        """
        story.append(Paragraph(overview_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Students summary table
        story.append(Paragraph("Student Activity Summary", self.styles['CustomHeading']))
        story.append(self.create_student_summary_table(students_data))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by APC Gym Log System", self.styles['Footer']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
