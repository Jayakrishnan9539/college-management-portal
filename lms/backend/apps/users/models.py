"""
User models for the LMS.

We use a single base User model (extends AbstractBaseUser) with a 'role' field.
Then Student, Faculty, Admin are separate profile models linked via OneToOne.
This keeps authentication simple while allowing role-specific data.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager to handle email-based login instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # automatically hashes with BCrypt
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Base user model used for authentication.
    Role determines whether the user is a Student, Faculty, or Admin.
    """

    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty'
        ADMIN = 'ADMIN', 'Admin'

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    # Token for password reset (stored temporarily)
    reset_token = models.UUIDField(null=True, blank=True)
    reset_token_created_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.name} ({self.role})"

    def generate_reset_token(self):
        """Generate a UUID token for password reset and save it."""
        self.reset_token = uuid.uuid4()
        self.reset_token_created_at = timezone.now()
        self.save(update_fields=['reset_token', 'reset_token_created_at'])
        return self.reset_token

    def is_reset_token_valid(self, token):
        """Check if the reset token is valid and not older than 1 hour."""
        if not self.reset_token or str(self.reset_token) != str(token):
            return False
        time_elapsed = timezone.now() - self.reset_token_created_at
        return time_elapsed.total_seconds() < 3600  # 1 hour


class Branch(models.TextChoices):
    CSE = 'CSE', 'Computer Science'
    ECE = 'ECE', 'Electronics & Communication'
    ME = 'ME', 'Mechanical Engineering'
    CE = 'CE', 'Civil Engineering'
    EE = 'EE', 'Electrical Engineering'


class Student(models.Model):
    """Student profile — linked to the base User account."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=50, choices=Branch.choices)
    semester = models.IntegerField()  # 1-8
    enrollment_year = models.IntegerField()
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'

    def __str__(self):
        return f"{self.roll_number} - {self.user.name}"

    @staticmethod
    def generate_roll_number(branch, enrollment_year):
        """Auto-generate roll number like CSE2024001."""
        count = Student.objects.filter(branch=branch, enrollment_year=enrollment_year).count() + 1
        return f"{branch}{enrollment_year}{count:03d}"


class Faculty(models.Model):
    """Faculty profile — linked to the base User account."""

    class Designation(models.TextChoices):
        PROFESSOR = 'Professor', 'Professor'
        ASSOCIATE = 'Associate Prof', 'Associate Professor'
        ASSISTANT = 'Assistant Prof', 'Assistant Professor'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    designation = models.CharField(max_length=50, choices=Designation.choices)
    department = models.CharField(max_length=50, choices=Branch.choices)
    qualification = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(default=0)

    class Meta:
        db_table = 'faculty_personal'

    def __str__(self):
        return f"{self.designation} {self.user.name} ({self.department})"


class Admin(models.Model):
    """Admin profile — linked to the base User account."""

    class AdminRole(models.TextChoices):
        SUPER_ADMIN = 'SuperAdmin', 'Super Admin'
        ADMIN = 'Admin', 'Admin'
        ACCOUNTANT = 'Accountant', 'Accountant'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    admin_role = models.CharField(max_length=50, choices=AdminRole.choices, default=AdminRole.ADMIN)

    class Meta:
        db_table = 'admins'

    def __str__(self):
        return f"{self.admin_role}: {self.user.name}"
