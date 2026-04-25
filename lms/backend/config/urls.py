"""
Main URL configuration for the LMS backend.
All API routes are prefixed with /api/
Swagger docs available at /swagger/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger / OpenAPI documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Landmine Soft LMS API",
        default_version='v1',
        description="College Management System API — Students, Faculty, Admin",
        contact=openapi.Contact(email="admin@landminesoft.edu"),
        license=openapi.License(name="Private"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes
    path('api/auth/', include('apps.users.urls.auth_urls')),
    path('api/student/', include('apps.users.urls.student_urls')),
    path('api/faculty/', include('apps.users.urls.faculty_urls')),
    path('api/admin/', include('apps.users.urls.admin_urls')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/marks/', include('apps.marks.urls')),
    path('api/fees/', include('apps.fees.urls')),
    path('api/announcements/', include('apps.announcements.urls')),

    # Swagger docs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
