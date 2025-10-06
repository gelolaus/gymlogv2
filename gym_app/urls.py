from django.urls import path
from . import views

urlpatterns = [
    # Student registration and login
    path('register/', views.StudentRegistrationView.as_view(), name='student_register'),
    path('login/', views.StudentLoginView.as_view(), name='student_login'),
    path('login/student-id/', views.StudentIDLoginView.as_view(), name='student_id_login'),
    path('check-status/<str:student_id>/', views.check_student_status, name='check_student_status'),
    
    # Gym check-in/check-out
    path('gym/checkinout/', views.GymCheckInOutView.as_view(), name='gym_checkinout'),
    
    # Student statistics and heatmap
    path('stats/rfid/', views.StudentRFIDStatsView.as_view(), name='student_rfid_stats'),
    path('stats/<str:student_id>/', views.StudentStatsView.as_view(), name='student_stats'),
    
    # PDF Export endpoints
    path('export/pdf/', views.PDFExportView.as_view(), name='pdf_export'),
    path('export/blocks/', views.get_available_blocks, name='available_blocks'),
    
    # Feedback endpoint
    path('feedback/', views.FeedbackView.as_view(), name='feedback'),
]
