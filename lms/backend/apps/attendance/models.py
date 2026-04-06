"""
Attendance model — tracks per-class attendance for each student.
Faculty marks attendance; students can view their own attendance percentage.
"""

from django.db import models
from django.utils import timezone
from apps.users.models import Student, Faculty
from apps.courses.models import Course


class Attendance(models.Model):
    class AttendanceStatus(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LEAVE = 'LEAVE', 'Leave'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    class_date = models.DateField()
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    marked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'attendance'
        unique_together = ['student', 'course', 'class_date']  # One record per student per class per day

    def __str__(self):
        return f"{self.student.roll_number} | {self.course} | {self.class_date} | {self.status}"
