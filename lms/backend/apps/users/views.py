"""
Authentication views: registration, login, password reset.
All responses follow a consistent format for the frontend to consume.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from apps.users.models import User, Student, Faculty
from apps.users.serializers import (
    StudentRegisterSerializer, FacultyRegisterSerializer, AdminRegisterSerializer,
    StudentLoginSerializer, FacultyLoginSerializer, AdminLoginSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    StudentProfileSerializer, StudentProfileUpdateSerializer, FacultyProfileSerializer,
)
from apps.users.permissions import IsStudent, IsFaculty, IsAdmin


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    # Add extra claims so the frontend knows who is logged in
    refresh['role'] = user.role
    refresh['name'] = user.name
    return {
        'token': str(refresh.access_token),
        'refresh': str(refresh),
        'type': 'Bearer',
        'userId': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
    }


# ─── Registration Views ───────────────────────────────────────────────────────

class StudentRegisterView(APIView):
    """POST /api/auth/student/register — open to anyone."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            student = user.student_profile
            return Response({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'roll_number': student.roll_number,
                'role': user.role,
                'message': 'Registration successful. Please login.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FacultyRegisterView(APIView):
    """POST /api/auth/faculty/register — admin only."""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = FacultyRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'message': 'Faculty account created successfully.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminRegisterView(APIView):
    """POST /api/auth/admin/register — SuperAdmin only."""
    permission_classes = [IsAdmin]

    def post(self, request):
        # Only SuperAdmins can create other admins
        if hasattr(request.user, 'admin_profile'):
            if request.user.admin_profile.admin_role != 'SuperAdmin':
                return Response(
                    {'error': 'Only SuperAdmins can create admin accounts.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer = AdminRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'message': 'Admin account created successfully.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Login Views ──────────────────────────────────────────────────────────────

class StudentLoginView(APIView):
    """POST /api/auth/student/login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(get_tokens_for_user(user), status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class FacultyLoginView(APIView):
    """POST /api/auth/faculty/login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FacultyLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(get_tokens_for_user(user), status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class AdminLoginView(APIView):
    """POST /api/auth/admin/login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(get_tokens_for_user(user), status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


# ─── Password Management ──────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """POST /api/auth/forgot-password — sends reset link via email."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = user.generate_reset_token()
                reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

                send_mail(
                    subject='Password Reset — LMS College Portal',
                    message=f"""
Hi {user.name},

You requested a password reset. Click the link below to reset your password:

{reset_url}

This link is valid for 1 hour. If you didn't request this, please ignore this email.

— Landmine Soft College Portal
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except User.DoesNotExist:
                pass  # Don't reveal whether the email exists

        # Always respond with success to prevent user enumeration
        return Response({'message': 'If this email is registered, a reset link has been sent.'})


class ResetPasswordView(APIView):
    """POST /api/auth/reset-password — uses the token from email."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            try:
                user = User.objects.get(reset_token=token)
                if not user.is_reset_token_valid(token):
                    return Response(
                        {'error': 'Reset link has expired. Please request a new one.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.set_password(new_password)
                user.reset_token = None
                user.reset_token_created_at = None
                user.save()
                return Response({'message': 'Password reset successful. You can now login.'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """POST /api/auth/change-password — for logged-in users."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({'message': 'Password changed successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Profile Views ────────────────────────────────────────────────────────────

class StudentProfileView(APIView):
    """GET/PUT /api/student/profile"""
    permission_classes = [IsStudent]

    def get(self, request):
        student = request.user.student_profile
        serializer = StudentProfileSerializer(student)
        return Response(serializer.data)

    def put(self, request):
        student = request.user.student_profile
        serializer = StudentProfileUpdateSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return updated full profile
            return Response(StudentProfileSerializer(student).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FacultyProfileView(APIView):
    """GET /api/faculty/profile"""
    permission_classes = [IsFaculty]

    def get(self, request):
        faculty = request.user.faculty_profile
        serializer = FacultyProfileSerializer(faculty)
        return Response(serializer.data)
