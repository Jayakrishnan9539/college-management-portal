from django.urls import path
from apps.users.views import FacultyProfileView

urlpatterns = [
    path('profile/', FacultyProfileView.as_view(), name='faculty-profile'),
]