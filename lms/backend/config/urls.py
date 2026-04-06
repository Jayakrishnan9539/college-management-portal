from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

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
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)