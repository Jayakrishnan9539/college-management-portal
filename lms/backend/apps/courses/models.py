"""
Course-related models: Subject (what is taught), Course (who teaches it, which section),
and Enrollment (which students are in which courses).
"""

from django.db import models
from django.utils import timezone
from apps.users.models import Student, Faculty


class Subject(models.Model):
    """
    A subject is a course unit like 'Data Structures (CS201)'.
    It belongs to a branch and semester.
    """
    subject_code = models.CharField(max_length=20, unique=True)  # e.g. CS201
    subject_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    semester = models.IntegerField()
    credits = models.IntegerField(default=3)
    theory_marks = models.IntegerField(default=100)
    practical_marks = models.IntegerField(default=50)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return f"{self.subject_code} — {self.subject_name}"


class Course(models.Model):
    """
    A course is when a specific faculty teaches a specific subject
    to a specific section in a specific academic year.
    
    e.g., Prof. Sharma teaches CS201 to section A in 2024-25.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='courses')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    semester = models.IntegerField()
    section = models.CharField(max_length=10, default='A')  # A, B, C
    academic_year = models.CharField(max_length=10)  # e.g. "2024-25"
    total_classes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'courses'
        unique_together = ['faculty', 'subject', 'section', 'academic_year']

    def __str__(self):
        return f"{self.subject.subject_code} | {self.faculty.user.name} | Sec {self.section}"


class Enrollment(models.Model):
    """
    Records which students are enrolled in which courses.
    A student can drop or complete a course — tracked by status.
    """
    class EnrollmentStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DROPPED = 'DROPPED', 'Dropped'
        COMPLETED = 'COMPLETED', 'Completed'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)
    enrolled_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'course', 'academic_year']

    def __str__(self):
        return f"{self.student.roll_number} → {self.course}"
