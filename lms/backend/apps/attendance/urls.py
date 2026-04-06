from django.urls import path
from .views import MarkAttendanceView, StudentAttendanceView, CourseAttendanceReportView

urlpatterns = [
    path('mark/', MarkAttendanceView.as_view(), name='mark-attendance'),
    path('my/', StudentAttendanceView.as_view(), name='my-attendance'),
    path('course/<int:course_id>/', CourseAttendanceReportView.as_view(), name='course-attendance'),
]