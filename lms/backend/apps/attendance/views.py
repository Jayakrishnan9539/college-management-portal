"""
Attendance views:
- Faculty marks attendance for a class
- Students view their own attendance summary
- Admin views overall attendance reports
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db.models import Count, Q
from .models import Attendance
from apps.courses.models import Course, Enrollment
from apps.users.models import Student
from apps.users.permissions import IsFaculty, IsStudent, IsAdmin


# ─── Serializers ──────────────────────────────────────────────────────────────

class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.name', read_only=True)
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'roll_number', 'course',
                  'class_date', 'status', 'marked_by', 'created_at']


class BulkAttendanceSerializer(serializers.Serializer):
    """Faculty submits attendance for an entire class in one request."""
    course_id = serializers.IntegerField()
    class_date = serializers.DateField()
    records = serializers.ListField(
        child=serializers.DictField()  # [{"student_id": 1, "status": "PRESENT"}, ...]
    )


# ─── Views ────────────────────────────────────────────────────────────────────

class MarkAttendanceView(APIView):
    """
    POST /api/attendance/mark
    Faculty submits attendance for all students in a course on a given date.
    """
    permission_classes = [IsFaculty]

    def post(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        faculty = request.user.faculty_profile
        course_id = serializer.validated_data['course_id']
        class_date = serializer.validated_data['class_date']
        records = serializer.validated_data['records']

        # Verify this course belongs to this faculty
        try:
            course = Course.objects.get(id=course_id, faculty=faculty)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found or not assigned to you.'}, status=404)

        created_count = 0
        updated_count = 0

        for record in records:
            student_id = record.get('student_id')
            att_status = record.get('status', 'PRESENT')

            if att_status not in ['PRESENT', 'ABSENT', 'LEAVE']:
                continue

            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                continue

            obj, created = Attendance.objects.update_or_create(
                student=student,
                course=course,
                class_date=class_date,
                defaults={'status': att_status, 'marked_by': faculty}
            )

            # Update total classes count on first time marking for this date
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Increment total classes count on course if this is a new date
        existing_dates = Attendance.objects.filter(course=course).values('class_date').distinct().count()
        course.total_classes = existing_dates
        course.save(update_fields=['total_classes'])

        return Response({
            'message': f'Attendance marked. {created_count} new, {updated_count} updated.',
            'course_id': course_id,
            'class_date': str(class_date),
        })


class StudentAttendanceView(APIView):
    """
    GET /api/attendance/my
    Student views their attendance summary — total classes, present, percentage per course.
    """
    permission_classes = [IsStudent]

    def get(self, request):
        student = request.user.student_profile
        course_id = request.query_params.get('course_id')

        # Get all active enrollments for this student
        enrollments = Enrollment.objects.filter(
            student=student, status='ACTIVE'
        ).select_related('course__subject')

        summary = []
        for enrollment in enrollments:
            course = enrollment.course

            if course_id and str(course.id) != str(course_id):
                continue

            total = Attendance.objects.filter(student=student, course=course).count()
            present = Attendance.objects.filter(student=student, course=course, status='PRESENT').count()
            absent = Attendance.objects.filter(student=student, course=course, status='ABSENT').count()
            on_leave = Attendance.objects.filter(student=student, course=course, status='LEAVE').count()

            percentage = round((present / total * 100), 2) if total > 0 else 0
            is_short = percentage < 75  # Flag if attendance is below 75%

            summary.append({
                'course_id': course.id,
                'subject_code': course.subject.subject_code,
                'subject_name': course.subject.subject_name,
                'total_classes': course.total_classes,
                'attended': present,
                'absent': absent,
                'on_leave': on_leave,
                'percentage': percentage,
                'is_short_attendance': is_short,
            })

        return Response(summary)


class CourseAttendanceReportView(APIView):
    """
    GET /api/attendance/course/<course_id>
    Faculty views detailed attendance report for their course.
    """
    permission_classes = [IsFaculty]

    def get(self, request, course_id):
        faculty = request.user.faculty_profile
        try:
            course = Course.objects.get(id=course_id, faculty=faculty)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=404)

        class_date = request.query_params.get('date')

        records = Attendance.objects.filter(course=course).select_related('student__user')
        if class_date:
            records = records.filter(class_date=class_date)

        serializer = AttendanceRecordSerializer(records, many=True)
        return Response({
            'course': str(course),
            'total_classes': course.total_classes,
            'records': serializer.data,
        })
