"""Tests for notification preferences API (#21)."""

import pytest
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, Organization, User
from apps.notifications.models import NotificationPreference


def _authed_client(user: User) -> Client:
    c = Client()
    c.defaults["HTTP_AUTHORIZATION"] = f"Bearer {RefreshToken.for_user(user).access_token}"
    return c


@pytest.fixture
def org():
    return Organization.objects.create(
        name="Pref Org", slug="pref-org", primary_email="owner@pref.com"
    )


@pytest.fixture
def user(org):
    u = User.objects.create_user(
        email="owner@pref.com",
        password="strongpassword1",  # pragma: allowlist secret
        first_name="Owner",
    )
    Membership.objects.create(user=u, organization=org, role=Membership.Role.OWNER)
    u.active_organization = org
    u.save(update_fields=["active_organization"])
    return u


@pytest.fixture
def client_(user):
    return _authed_client(user)


@pytest.mark.django_db
class TestGetPreferences:
    def test_returns_all_combinations_with_defaults(self, client_):
        resp = client_.get("/api/v1/notifications/preferences/")
        assert resp.status_code == 200
        data = resp.json()
        # 3 events × 2 channels = 6 items
        assert len(data) == 6
        # All default to enabled
        assert all(item["enabled"] for item in data)

    def test_reflects_saved_preference(self, client_, user):
        NotificationPreference.objects.create(
            user=user, event_type="bill.issued", channel="email", enabled=False
        )
        resp = client_.get("/api/v1/notifications/preferences/")
        assert resp.status_code == 200
        item = next(
            i for i in resp.json() if i["event_type"] == "bill.issued" and i["channel"] == "email"
        )
        assert item["enabled"] is False

    def test_unauthenticated_returns_401(self):
        resp = Client().get("/api/v1/notifications/preferences/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestUpdatePreferences:
    def _full_payload(self, overrides: dict) -> list:
        from apps.notifications.models import PREFERENCE_CHANNELS, PREFERENCE_EVENTS

        return [
            {
                "event_type": evt,
                "channel": ch,
                "enabled": overrides.get((evt, ch), True),
            }
            for evt, _ in PREFERENCE_EVENTS
            for ch, _ in PREFERENCE_CHANNELS
        ]

    def test_put_updates_preferences(self, client_, user):
        payload = self._full_payload({("bill.issued", "email"): False})
        resp = client_.put(
            "/api/v1/notifications/preferences/",
            payload,
            content_type="application/json",
        )
        assert resp.status_code == 200
        item = next(
            i for i in resp.json() if i["event_type"] == "bill.issued" and i["channel"] == "email"
        )
        assert item["enabled"] is False
        assert (
            NotificationPreference.objects.get(
                user=user, event_type="bill.issued", channel="email"
            ).enabled
            is False
        )

    def test_put_is_idempotent(self, client_):
        payload = self._full_payload({("payment.received", "sms"): False})
        resp1 = client_.put(
            "/api/v1/notifications/preferences/",
            payload,
            content_type="application/json",
        )
        resp2 = client_.put(
            "/api/v1/notifications/preferences/",
            payload,
            content_type="application/json",
        )
        assert resp1.status_code == resp2.status_code == 200
        assert resp1.json() == resp2.json()

    def test_put_rejects_unknown_event_type(self, client_):
        resp = client_.put(
            "/api/v1/notifications/preferences/",
            [{"event_type": "unknown.event", "channel": "email", "enabled": True}],
            content_type="application/json",
        )
        assert resp.status_code == 400
