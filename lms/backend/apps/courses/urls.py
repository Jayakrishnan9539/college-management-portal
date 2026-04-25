from django.urls import path
from .views import (
    SubjectListCreateView, SubjectDetailView,
    CourseListCreateView, FacultyCourseListView,
    StudentEnrollmentView, DropEnrollmentView,
)

urlpatterns = [
    path('subjects', SubjectListCreateView.as_view(), name='subjects'),
    path('subjects/<int:pk>', SubjectDetailView.as_view(), name='subject-detail'),
    path('', CourseListCreateView.as_view(), name='courses'),
    path('my-courses', FacultyCourseListView.as_view(), name='faculty-courses'),
    path('enrollments', StudentEnrollmentView.as_view(), name='enrollments'),
    path('enrollments/<int:pk>', DropEnrollmentView.as_view(), name='drop-enrollment'),
]
