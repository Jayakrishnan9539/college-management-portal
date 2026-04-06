from django.urls import path
from .models_views import EnterMarksView, StudentMarksView, CourseMarksView

urlpatterns = [
    path('my/', StudentMarksView.as_view(), name='my-marks'),
    path('course/<int:course_id>/', CourseMarksView.as_view(), name='course-marks'),
    path('course/<int:course_id>/enter/', EnterMarksView.as_view(), name='enter-marks'),
]