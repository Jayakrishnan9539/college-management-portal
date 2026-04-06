"""
Custom permission classes for role-based access control.
Usage: Add @permission_classes([IsStudent]) to any view.
"""

from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """Only authenticated students can access this endpoint."""
    message = "This endpoint is for students only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'STUDENT'
        )


class IsFaculty(BasePermission):
    """Only authenticated faculty members can access this endpoint."""
    message = "This endpoint is for faculty only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'FACULTY'
        )


class IsAdmin(BasePermission):
    """Only authenticated admins can access this endpoint."""
    message = "This endpoint is for admins only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsStudentOrFaculty(BasePermission):
    """Both students and faculty can access this endpoint."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['STUDENT', 'FACULTY']
        )


class IsAdminOrFaculty(BasePermission):
    """Both admins and faculty can access this endpoint."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'FACULTY']
        )
