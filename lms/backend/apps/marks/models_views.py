"""
Marks module — faculty enters marks, students view their grades and results.
Grade is auto-calculated based on total_marks percentage.
"""

from django.db import models
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from apps.users.models import Student, Faculty
from apps.courses.models import Subject, Course
from apps.users.permissions import IsFaculty, IsStudent, IsAdmin


# ─── Model ────────────────────────────────────────────────────────────────────

def calculate_grade(percentage):
    """Auto-calculate grade from percentage."""
    if percentage >= 90: return 'A+'
    if percentage >= 80: return 'A'
    if percentage >= 70: return 'B+'
    if percentage >= 60: return 'B'
    if percentage >= 50: return 'C'
    if percentage >= 40: return 'D'
    return 'F'


class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='marks')
    theory_marks = models.IntegerField(default=0)
    practical_marks = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    grade = models.CharField(max_length=5, blank=True)
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marks'
        unique_together = ['student', 'course', 'academic_year']

    def save(self, *args, **kwargs):
        # Auto-calculate total and grade before saving
        self.total_marks = self.theory_marks + self.practical_marks
        max_marks = self.subject.theory_marks + self.subject.practical_marks
        if max_marks > 0:
            percentage = (self.total_marks / max_marks) * 100
            self.grade = calculate_grade(percentage)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.roll_number} | {self.subject.subject_code} | {self.grade}"


# ─── Serializers ──────────────────────────────────────────────────────────────

class MarksSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    max_theory = serializers.IntegerField(source='subject.theory_marks', read_only=True)
    max_practical = serializers.IntegerField(source='subject.practical_marks', read_only=True)

    class Meta:
        model = Marks
        fields = ['id', 'subject', 'subject_name', 'subject_code',
                  'theory_marks', 'practical_marks', 'total_marks', 'grade',
                  'max_theory', 'max_practical', 'semester', 'academic_year', 'updated_at']


class EnterMarksSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    theory_marks = serializers.IntegerField(min_value=0)
    practical_marks = serializers.IntegerField(min_value=0, default=0)
    academic_year = serializers.CharField(max_length=10)


# ─── Views ────────────────────────────────────────────────────────────────────

class EnterMarksView(APIView):
    """POST /api/marks/course/<course_id> — faculty enters marks for a student."""
    permission_classes = [IsFaculty]

    def post(self, request, course_id):
        faculty = request.user.faculty_profile
        try:
            course = Course.objects.select_related('subject').get(id=course_id, faculty=faculty)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found or not assigned to you.'}, status=404)

        serializer = EnterMarksSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        # Validate marks don't exceed subject maximum
        if data['theory_marks'] > course.subject.theory_marks:
            return Response({'error': f'Theory marks cannot exceed {course.subject.theory_marks}.'}, status=400)
        if data['practical_marks'] > course.subject.practical_marks:
            return Response({'error': f'Practical marks cannot exceed {course.subject.practical_marks}.'}, status=400)

        try:
            student = Student.objects.get(id=data['student_id'])
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=404)

        marks_obj, created = Marks.objects.update_or_create(
            student=student,
            course=course,
            academic_year=data['academic_year'],
            defaults={
                'subject': course.subject,
                'theory_marks': data['theory_marks'],
                'practical_marks': data['practical_marks'],
                'semester': course.semester,
            }
        )

        return Response(MarksSerializer(marks_obj).data, status=201 if created else 200)


class StudentMarksView(APIView):
    """GET /api/marks/my — student views their marks and grades."""
    permission_classes = [IsStudent]

    def get(self, request):
        student = request.user.student_profile
        semester = request.query_params.get('semester')
        academic_year = request.query_params.get('academic_year')

        marks = Marks.objects.filter(student=student).select_related('subject')
        if semester:
            marks = marks.filter(semester=semester)
        if academic_year:
            marks = marks.filter(academic_year=academic_year)

        # Calculate CGPA
        all_marks = list(marks)
        total_credits = sum(m.subject.credits for m in all_marks)
        grade_points = {'A+': 10, 'A': 9, 'B+': 8, 'B': 7, 'C': 6, 'D': 5, 'F': 0}
        if total_credits > 0:
            weighted = sum(
                grade_points.get(m.grade, 0) * m.subject.credits for m in all_marks
            )
            cgpa = round(weighted / total_credits, 2)
        else:
            cgpa = 0

        return Response({
            'marks': MarksSerializer(marks, many=True).data,
            'cgpa': cgpa,
            'total_credits': total_credits,
        })


class CourseMarksView(APIView):
    """GET /api/marks/course/<course_id> — faculty views all marks for their course."""
    permission_classes = [IsFaculty]

    def get(self, request, course_id):
        faculty = request.user.faculty_profile
        try:
            course = Course.objects.get(id=course_id, faculty=faculty)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=404)

        marks = Marks.objects.filter(course=course).select_related('student__user', 'subject')
        data = []
        for m in marks:
            data.append({
                'student_id': m.student.id,
                'roll_number': m.student.roll_number,
                'student_name': m.student.user.name,
                'theory_marks': m.theory_marks,
                'practical_marks': m.practical_marks,
                'total_marks': m.total_marks,
                'grade': m.grade,
            })
        return Response({'course': str(course), 'results': data})
