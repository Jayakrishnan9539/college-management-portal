"""
Course views: Subject CRUD, Course management, Student enrollment.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Subject, Course, Enrollment
from .serializers import SubjectSerializer, CourseSerializer, EnrollmentSerializer, EnrollStudentSerializer
from apps.users.permissions import IsAdmin, IsFaculty, IsStudent, IsAdminOrFaculty
from rest_framework.permissions import IsAuthenticated
from apps.users.models import Student


class SubjectListCreateView(APIView):
    """GET /api/courses/subjects — list all; POST — admin creates a subject."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAuthenticated()]  # anyone authenticated can view

    def get(self, request):
        branch = request.query_params.get('branch')
        semester = request.query_params.get('semester')
        subjects = Subject.objects.all()
        if branch:
            subjects = subjects.filter(branch=branch)
        if semester:
            subjects = subjects.filter(semester=semester)
        return Response(SubjectSerializer(subjects, many=True).data)

    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectDetailView(APIView):
    """GET/PUT/DELETE /api/courses/subjects/<id>"""
    permission_classes = [IsAdmin]

    def get_object(self, pk):
        try:
            return Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return None

    def get(self, request, pk):
        subject = self.get_object(pk)
        if not subject:
            return Response({'error': 'Subject not found.'}, status=404)
        return Response(SubjectSerializer(subject).data)

    def put(self, request, pk):
        subject = self.get_object(pk)
        if not subject:
            return Response({'error': 'Subject not found.'}, status=404)
        serializer = SubjectSerializer(subject, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        subject = self.get_object(pk)
        if not subject:
            return Response({'error': 'Subject not found.'}, status=404)
        subject.delete()
        return Response({'message': 'Subject deleted.'}, status=204)


class CourseListCreateView(APIView):
    """GET all courses / POST create a course (admin assigns faculty to subject)."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return []

    def get(self, request):
        semester = request.query_params.get('semester')
        academic_year = request.query_params.get('academic_year')
        courses = Course.objects.select_related('subject', 'faculty__user').all()
        if semester:
            courses = courses.filter(semester=semester)
        if academic_year:
            courses = courses.filter(academic_year=academic_year)
        return Response(CourseSerializer(courses, many=True).data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class FacultyCourseListView(APIView):
    """GET /api/courses/my-courses — courses assigned to the logged-in faculty."""
    permission_classes = [IsFaculty]

    def get(self, request):
        faculty = request.user.faculty_profile
        courses = Course.objects.filter(faculty=faculty).select_related('subject')
        return Response(CourseSerializer(courses, many=True).data)


class StudentEnrollmentView(APIView):
    """
    GET  /api/courses/enrollments  — student sees their enrollments
    POST /api/courses/enrollments  — student enrolls in a course
    """
    permission_classes = [IsStudent]

    def get(self, request):
        student = request.user.student_profile
        enrollments = Enrollment.objects.filter(
            student=student, status='ACTIVE'
        ).select_related('subject', 'course__faculty__user')
        return Response(EnrollmentSerializer(enrollments, many=True).data)

    def post(self, request):
        serializer = EnrollStudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        student = request.user.student_profile
        try:
            course = Course.objects.select_related('subject').get(
                id=serializer.validated_data['course_id']
            )
        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=404)

        # Prevent duplicate enrollments
        if Enrollment.objects.filter(student=student, course=course, status='ACTIVE').exists():
            return Response({'error': 'You are already enrolled in this course.'}, status=400)

        enrollment = Enrollment.objects.create(
            student=student,
            subject=course.subject,
            course=course,
            semester=student.semester,
            academic_year=serializer.validated_data['academic_year'],
        )
        return Response(EnrollmentSerializer(enrollment).data, status=201)


class DropEnrollmentView(APIView):
    """DELETE /api/courses/enrollments/<id> — student drops a course."""
    permission_classes = [IsStudent]

    def delete(self, request, pk):
        try:
            enrollment = Enrollment.objects.get(pk=pk, student=request.user.student_profile)
        except Enrollment.DoesNotExist:
            return Response({'error': 'Enrollment not found.'}, status=404)
        enrollment.status = 'DROPPED'
        enrollment.save()
        return Response({'message': 'Course dropped successfully.'})
