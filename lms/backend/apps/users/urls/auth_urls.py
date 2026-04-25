from django.urls import path
from apps.users.views import (
    StudentRegisterView, FacultyRegisterView, AdminRegisterView,
    StudentLoginView, FacultyLoginView, AdminLoginView,
    ForgotPasswordView, ResetPasswordView, ChangePasswordView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Registration
    path('student/register', StudentRegisterView.as_view(), name='student-register'),
    path('faculty/register', FacultyRegisterView.as_view(), name='faculty-register'),
    path('admin/register', AdminRegisterView.as_view(), name='admin-register'),

    # Login
    path('student/login', StudentLoginView.as_view(), name='student-login'),
    path('faculty/login', FacultyLoginView.as_view(), name='faculty-login'),
    path('admin/login', AdminLoginView.as_view(), name='admin-login'),

    # Password management
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),

    # JWT refresh
    path('token/refresh', TokenRefreshView.as_view(), name='token-refresh'),
]
