"""Notifications views — user's own notifications + preference management."""

from rest_framework import filters, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import (
    PREFERENCE_CHANNELS,
    PREFERENCE_EVENTS,
    Notification,
    NotificationPreference,
)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "channel",
            "event_type",
            "subject",
            "body",
            "status",
            "sent_at",
            "read_at",
            "created_at",
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
        Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
            read_at=now, status=Notification.Status.READ
        )
        return Response({"status": "ok"})


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

_ALL_PAIRS = [(evt, ch) for evt, _ in PREFERENCE_EVENTS for ch, _ in PREFERENCE_CHANNELS]


class PreferenceItemSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=[e for e, _ in PREFERENCE_EVENTS])
    channel = serializers.ChoiceField(choices=[c for c, _ in PREFERENCE_CHANNELS])
    enabled = serializers.BooleanField()


class NotificationPreferencesView(APIView):
    """
    GET  /api/v1/notifications/preferences/  — return all event×channel toggles
    PUT  /api/v1/notifications/preferences/  — bulk-update toggles
    """

    permission_classes = [IsAuthenticated]

    def _get_preferences(self, user):
        """Return a complete list of preferences, filling defaults for any missing pairs."""
        existing = {
            (p.event_type, p.channel): p.enabled
            for p in NotificationPreference.objects.filter(user=user)
        }
        return [
            {
                "event_type": evt,
                "channel": ch,
                "enabled": existing.get((evt, ch), True),
            }
            for evt, ch in _ALL_PAIRS
        ]

    def get(self, request):
        return Response(self._get_preferences(request.user))

    def put(self, request):
        serializer = PreferenceItemSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        for item in serializer.validated_data:
            NotificationPreference.objects.update_or_create(
                user=request.user,
                event_type=item["event_type"],
                channel=item["channel"],
                defaults={"enabled": item["enabled"]},
            )
        return Response(self._get_preferences(request.user))
