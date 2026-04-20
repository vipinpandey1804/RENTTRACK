"""
Tenant context middleware.

Extracts organization_id from the authenticated user's JWT and
makes it available via thread-local storage for downstream code
(managers, signals, etc.). Also sets a Postgres session variable
that RLS policies can reference.
"""
import threading

from django.db import connection

_thread_locals = threading.local()


def get_current_organization_id():
    """Return the current request's organization_id, or None."""
    return getattr(_thread_locals, "organization_id", None)


def set_current_organization_id(org_id):
    _thread_locals.organization_id = org_id


class TenantContextMiddleware:
    """
    Sets the current organization context per request.

    Expects the JWT to include an `org` claim. Falls back to the user's
    active organization if a JWT claim isn't present (e.g., admin panel).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org_id = None
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            # Prefer JWT claim, then fall back to user's primary org
            auth = getattr(request, "auth", None)
            if auth and hasattr(auth, "get"):
                org_id = auth.get("org")
            if not org_id:
                org_id = getattr(user, "active_organization_id", None)

        set_current_organization_id(org_id)

        # Expose to Postgres for RLS policies (optional; uncomment when RLS is active)
        # if org_id:
        #     with connection.cursor() as cursor:
        #         cursor.execute("SELECT set_config('app.current_org', %s, true)", [str(org_id)])

        try:
            response = self.get_response(request)
        finally:
            set_current_organization_id(None)

        return response
