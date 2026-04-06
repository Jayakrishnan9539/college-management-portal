from django.db import models
from django.db.models import Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated


class Announcement(models.Model):
    class Audience(models.TextChoices):
        STUDENT = 'STUDENT', 'Students Only'
        FACULTY = 'FACULTY', 'Faculty Only'
        ALL = 'ALL', 'Everyone'

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements'
    )
    target_audience = models.CharField(
        max_length=20,
        choices=Audience.choices,
        default=Audience.ALL
    )
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


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.name',
        read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'description', 'created_by',
            'created_by_name', 'target_audience',
            'created_at', 'expires_at', 'is_active'
        ]
        read_only_fields = ['created_by']


class AnnouncementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        if role == 'STUDENT':
            announcements = Announcement.objects.filter(
                target_audience__in=['STUDENT', 'ALL']
            )
        elif role == 'FACULTY':
            announcements = Announcement.objects.filter(
                target_audience__in=['FACULTY', 'ALL']
            )
        else:
            announcements = Announcement.objects.all()

        today = timezone.now().date()
        announcements = announcements.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=today)
        )
        return Response(
            AnnouncementSerializer(announcements, many=True).data
        )

    def post(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can post announcements.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = AnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        # Print errors to help debug
        print("Announcement errors:", serializer.errors)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AnnouncementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return None

    def get(self, request, pk):
        ann = self.get_object(pk)
        if not ann:
            return Response(
                {'error': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(AnnouncementSerializer(ann).data)

    def put(self, request, pk):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Admin only.'},
                status=403
            )
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Not found.'}, status=404)
        serializer = AnnouncementSerializer(
            ann, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Admin only.'},
                status=403
            )
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Not found.'}, status=404)
        ann.delete()
        return Response({'message': 'Deleted.'}, status=204)