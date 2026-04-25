"""
Announcements — admin posts notices visible to students, faculty, or everyone.
"""

from django.db import models
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions import IsAdmin


# ─── Model ────────────────────────────────────────────────────────────────────

class Announcement(models.Model):
    class Audience(models.TextChoices):
        STUDENT = 'STUDENT', 'Students Only'
        FACULTY = 'FACULTY', 'Faculty Only'
        ALL = 'ALL', 'Everyone'

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='announcements')
    target_audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        if self.expires_at:
            return timezone.now().date() <= self.expires_at
        return True


# ─── Serializer ───────────────────────────────────────────────────────────────

class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'description', 'created_by', 'created_by_name',
                  'target_audience', 'created_at', 'expires_at', 'is_active']
        read_only_fields = ['created_by']


# ─── Views ────────────────────────────────────────────────────────────────────

class AnnouncementListView(APIView):
    """
    GET  /api/announcements  — view announcements relevant to the logged-in user
    POST /api/announcements  — admin creates an announcement
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        # Filter by audience — students see STUDENT + ALL, faculty see FACULTY + ALL
        if role == 'STUDENT':
            announcements = Announcement.objects.filter(target_audience__in=['STUDENT', 'ALL'])
        elif role == 'FACULTY':
            announcements = Announcement.objects.filter(target_audience__in=['FACULTY', 'ALL'])
        else:
            announcements = Announcement.objects.all()  # Admin sees everything

        # Only show active (non-expired) announcements
        today = timezone.now().date()
        announcements = announcements.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today)
        )

        return Response(AnnouncementSerializer(announcements, many=True).data)

    def post(self, request):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Only admins can post announcements.'}, status=403)

        serializer = AnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AnnouncementDetailView(APIView):
    """GET/PUT/DELETE /api/announcements/<id>"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return None

    def get(self, request, pk):
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=404)
        return Response(AnnouncementSerializer(ann).data)

    def put(self, request, pk):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Admin only.'}, status=403)
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=404)
        serializer = AnnouncementSerializer(ann, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Admin only.'}, status=403)
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=404)
        ann.delete()
        return Response({'message': 'Announcement deleted.'}, status=204)
