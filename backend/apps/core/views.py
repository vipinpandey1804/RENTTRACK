"""Health check endpoints for Kubernetes and uptime monitoring."""
from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def liveness(request):
    """Basic liveness probe — is the process running?"""
    return JsonResponse({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness(request):
    """Readiness probe — can we serve traffic? Checks DB."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ready", "db": "ok"})
    except Exception as exc:
        return JsonResponse(
            {"status": "not_ready", "db": "error", "error": str(exc)},
            status=503,
        )
