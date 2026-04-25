from django.urls import path
from apps.users.admin_views import AdminDashboardView, ListStudentsView, ListFacultyView, ManageStudentView

urlpatterns = [
    path('dashboard', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('students', ListStudentsView.as_view(), name='admin-list-students'),
    path('students/<int:student_id>', ManageStudentView.as_view(), name='admin-manage-student'),
    path('faculty', ListFacultyView.as_view(), name='admin-list-faculty'),
]
