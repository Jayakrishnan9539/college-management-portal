from django.urls import path
from .models_views import AnnouncementListView, AnnouncementDetailView

urlpatterns = [
    path('', AnnouncementListView.as_view(), name='announcements'),
    path('<int:pk>', AnnouncementDetailView.as_view(), name='announcement-detail'),
]
