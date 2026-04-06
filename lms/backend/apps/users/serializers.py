"""
Serializers for user registration, login, and profile management.
Handles validation (password strength, unique email, etc.)
"""

import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Student, Faculty, Admin


def validate_password_strength(password):
    """
    Password must be 8+ characters with at least:
    - 1 uppercase letter
    - 1 number
    - 1 special character
    """
    if len(password) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'\d', password):
        raise serializers.ValidationError("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        raise serializers.ValidationError("Password must contain at least one special character.")
    return password


# ─── Registration Serializers ────────────────────────────────────────────────

class StudentRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    branch = serializers.ChoiceField(choices=['CSE', 'ECE', 'ME', 'CE', 'EE'])
    enrollment_year = serializers.IntegerField(min_value=2000, max_value=2100)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def create(self, validated_data):
        # Create base user first
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            phone=validated_data['phone'],
            role=User.Role.STUDENT,
        )
        # Then create student profile with auto-generated roll number
        roll_number = Student.generate_roll_number(
            validated_data['branch'],
            validated_data['enrollment_year']
        )
        Student.objects.create(
            user=user,
            roll_number=roll_number,
            branch=validated_data['branch'],
            enrollment_year=validated_data['enrollment_year'],
            semester=1,  # New students start at semester 1
        )
        return user


class FacultyRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    department = serializers.ChoiceField(choices=['CSE', 'ECE', 'ME', 'CE', 'EE'])
    designation = serializers.ChoiceField(choices=['Professor', 'Associate Prof', 'Assistant Prof'])
    qualification = serializers.CharField(max_length=100, required=False, default='')
    experience_years = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            phone=validated_data['phone'],
            role=User.Role.FACULTY,
        )
        Faculty.objects.create(
            user=user,
            department=validated_data['department'],
            designation=validated_data['designation'],
            qualification=validated_data.get('qualification', ''),
            experience_years=validated_data.get('experience_years', 0),
        )
        return user


class AdminRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    admin_role = serializers.ChoiceField(choices=['SuperAdmin', 'Admin', 'Accountant'], default='Admin')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            phone=validated_data['phone'],
            role=User.Role.ADMIN,
            is_staff=True,
        )
        Admin.objects.create(
            user=user,
            admin_role=validated_data.get('admin_role', 'Admin'),
        )
        return user


# ─── Login Serializers ────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    expected_role = None  # Subclasses set this to enforce role-based login

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Your account is deactivated. Contact admin.")
        if self.expected_role and user.role != self.expected_role:
            raise serializers.ValidationError(f"This login is for {self.expected_role}s only.")
        data['user'] = user
        return data


class StudentLoginSerializer(LoginSerializer):
    expected_role = User.Role.STUDENT


class FacultyLoginSerializer(LoginSerializer):
    expected_role = User.Role.FACULTY


class AdminLoginSerializer(LoginSerializer):
    expected_role = User.Role.ADMIN


# ─── Profile Serializers ──────────────────────────────────────────────────────

class StudentProfileSerializer(serializers.ModelSerializer):
    """Read-only student profile with nested user info."""
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'name', 'email', 'phone', 'role', 'roll_number',
                  'branch', 'semester', 'enrollment_year', 'dob',
                  'address', 'city', 'pincode']


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """Allows students to update only certain fields of their profile."""
    phone = serializers.CharField(source='user.phone', required=False)

    class Meta:
        model = Student
        fields = ['phone', 'dob', 'address', 'city', 'pincode']

    def update(self, instance, validated_data):
        # Handle nested user phone update
        user_data = validated_data.pop('user', {})
        if 'phone' in user_data:
            instance.user.phone = user_data['phone']
            instance.user.save(update_fields=['phone'])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class FacultyProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Faculty
        fields = ['id', 'name', 'email', 'phone', 'role',
                  'designation', 'department', 'qualification', 'experience_years']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Current password is incorrect."})
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)
