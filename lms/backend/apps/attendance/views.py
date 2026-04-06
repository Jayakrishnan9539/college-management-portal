from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from .models import Attendance
from apps.courses.models import Course, Enrollment
from apps.users.models import Student
from apps.users.permissions import IsFaculty, IsStudent


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.name', read_only=True)
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'roll_number', 'course',
                  'class_date', 'status', 'marked_by', 'created_at']


class BulkAttendanceSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    class_date = serializers.DateField()
    records = serializers.ListField(child=serializers.DictField())


class MarkAttendanceView(APIView):
    permission_classes = [IsFaculty]

    def post(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        faculty = request.user.faculty_profile
        course_id = serializer.validated_data['course_id']
        class_date = serializer.validated_data['class_date']
        records = serializer.validated_data['records']

        try:
            course = Course.objects.get(id=course_id, faculty=faculty)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found or not assigned to you.'},
                status=404
            )

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
            if created:
                created_count += 1
            else:
                updated_count += 1

        existing_dates = Attendance.objects.filter(
            course=course
        ).values('class_date').distinct().count()
        course.total_classes = existing_dates
        course.save(update_fields=['total_classes'])

        return Response({
            'message': f'Attendance marked. {created_count} new, {updated_count} updated.',
            'course_id': course_id,
            'class_date': str(class_date),
        })


class StudentAttendanceView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        student = request.user.student_profile
        enrollments = Enrollment.objects.filter(
            student=student, status='ACTIVE'
        ).select_related('course__subject')

        summary = []
        for enrollment in enrollments:
            course = enrollment.course
            total = Attendance.objects.filter(
                student=student, course=course
            ).count()
            present = Attendance.objects.filter(
                student=student, course=course, status='PRESENT'
            ).count()
            absent = Attendance.objects.filter(
                student=student, course=course, status='ABSENT'
            ).count()
            on_leave = Attendance.objects.filter(
                student=student, course=course, status='LEAVE'
            ).count()
            percentage = round((present / total * 100), 2) if total > 0 else 0

            summary.append({
                'course_id': course.id,
                'subject_code': course.subject.subject_code,
                'subject_name': course.subject.subject_name,
                'total_classes': course.total_classes,
                'attended': present,
                'absent': absent,
                'on_leave': on_leave,
                'percentage': percentage,
                'is_short_attendance': percentage < 75,
            })

        return Response(summary)


class CourseAttendanceReportView(APIView):
    permission_classes = [IsFaculty]

    def get(self, request, course_id):
        print("USER:", request.user.email, "ROLE:", request.user.role)
        faculty = request.user.faculty_profile

        try:
            course = Course.objects.get(id=course_id, faculty=faculty)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=404)

        class_date = request.query_params.get('date')

        # Get ALL students enrolled in this course
        enrollments = Enrollment.objects.filter(
            course=course
        ).select_related('student__user')

        print("Total enrollments (no status filter):", enrollments.count())

        # Also try with status filter
        active_enrollments = enrollments.filter(status='ACTIVE')
        print("Active enrollments:", active_enrollments.count())

        # Use all enrollments if active is empty
        final_enrollments = active_enrollments if active_enrollments.count() > 0 else enrollments

        # Get existing attendance for this date
        existing = {}
        if class_date:
            att_records = Attendance.objects.filter(
                course=course, class_date=class_date
            )
            for a in att_records:
                existing[a.student_id] = a.status

        # Build records from enrollments
        records = []
        for enrollment in final_enrollments:
            student = enrollment.student
            print("Adding student:", student.user.name, student.roll_number)
            records.append({
                'id': None,
                'student': student.id,
                'student_name': student.user.name,
                'roll_number': student.roll_number,
                'course': course.id,
                'class_date': class_date,
                'status': existing.get(student.id, 'PRESENT'),
                'marked_by': None,
                'created_at': None,
            })

        print("Total records being returned:", len(records))

        return Response({
            'course': str(course),
            'total_classes': course.total_classes,
            'records': records,
        })