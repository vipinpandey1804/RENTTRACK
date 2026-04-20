"""Notifications views — tenant can list their own notifications."""
from rest_framework import filters, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "channel", "event_type", "subject", "body",
            "status", "sent_at", "read_at", "created_at",
        ]
        read_only_fields = ["id", "sent_at", "read_at", "created_at"]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """A user's own notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("recipient")

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        from django.utils import timezone
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.status = Notification.Status.READ
            notification.save(update_fields=["read_at", "status"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        from django.utils import timezone
        now = timezone.now()
        Notification.objects.filter(
            recipient=request.user, read_at__isnull=True
        ).update(read_at=now, status=Notification.Status.READ)
        return Response({"status": "ok"})
