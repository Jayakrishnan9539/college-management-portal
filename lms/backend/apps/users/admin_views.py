"""
Admin views for managing the college — listing students, faculty, dashboard stats.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import Student, Faculty, User
from apps.users.serializers import StudentProfileSerializer, FacultyProfileSerializer
from apps.users.permissions import IsAdmin
from apps.courses.models import Course
from apps.attendance.models import Attendance
from apps.fees.models import FeePayment


class AdminDashboardView(APIView):
    """GET /api/admin/dashboard — summary stats for the admin panel."""
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            'total_students': Student.objects.count(),
            'total_faculty': Faculty.objects.count(),
            'total_courses': Course.objects.count(),
            'pending_fee_payments': FeePayment.objects.filter(payment_status='PENDING').count(),
            'total_fee_collected': sum(
                p.amount_paid for p in FeePayment.objects.filter(payment_status='COMPLETED')
            ),
        })


class ListStudentsView(APIView):
    """GET /api/admin/students — paginated list of all students."""
    permission_classes = [IsAdmin]

    def get(self, request):
        branch = request.query_params.get('branch')
        semester = request.query_params.get('semester')

        students = Student.objects.select_related('user').all()
        if branch:
            students = students.filter(branch=branch)
        if semester:
            students = students.filter(semester=semester)

        serializer = StudentProfileSerializer(students, many=True)
        return Response({'count': students.count(), 'students': serializer.data})


class ManageStudentView(APIView):
    """GET/PUT/DELETE /api/admin/students/<id> — view or update a specific student."""
    permission_classes = [IsAdmin]

    def get_student(self, student_id):
        try:
            return Student.objects.select_related('user').get(id=student_id)
        except Student.DoesNotExist:
            return None

    def get(self, request, student_id):
        student = self.get_student(student_id)
        if not student:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StudentProfileSerializer(student).data)

    def put(self, request, student_id):
        """Admin can update semester, branch, etc."""
        student = self.get_student(student_id)
        if not student:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        allowed_fields = ['semester', 'branch']
        for field in allowed_fields:
            if field in request.data:
                setattr(student, field, request.data[field])
        student.save()
        return Response({'message': 'Student updated.', 'student': StudentProfileSerializer(student).data})

    def delete(self, request, student_id):
        """Deactivate student (soft delete — don't actually remove data)."""
        student = self.get_student(student_id)
        if not student:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        student.user.is_active = False
        student.user.save()
        return Response({'message': 'Student account deactivated.'})


class ListFacultyView(APIView):
    """GET /api/admin/faculty"""
    permission_classes = [IsAdmin]

    def get(self, request):
        department = request.query_params.get('department')
        faculty = Faculty.objects.select_related('user').all()
        if department:
            faculty = faculty.filter(department=department)
        serializer = FacultyProfileSerializer(faculty, many=True)
        return Response({'count': faculty.count(), 'faculty': serializer.data})
