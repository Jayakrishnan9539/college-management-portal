from rest_framework import serializers
from .models import Subject, Course, Enrollment


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    faculty_name = serializers.CharField(source='faculty.user.name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'subject', 'subject_name', 'subject_code', 'faculty', 'faculty_name',
                  'semester', 'section', 'academic_year', 'total_classes', 'created_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    faculty_name = serializers.CharField(source='course.faculty.user.name', read_only=True)
    section = serializers.CharField(source='course.section', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'subject', 'subject_name', 'subject_code', 'course',
                  'faculty_name', 'section', 'semester', 'academic_year', 'status', 'enrolled_date']


class EnrollStudentSerializer(serializers.Serializer):
    """Used when enrolling a student into a course."""
    course_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=10)
