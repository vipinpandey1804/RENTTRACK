"""Tests for tenant invite flow (Issue #7)."""
import pytest
from django.utils import timezone

from apps.accounts.models import Invite, Membership, User


@pytest.mark.django_db
class TestInviteCreation:
    def test_owner_can_create_invite(self, owner_client, org):
        resp = owner_client.post(
            "/api/v1/auth/invite/",
            {"email": "newtenant@test.com", "role": "tenant"},
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.data["email"] == "newtenant@test.com"
        assert Invite.objects.filter(email="newtenant@test.com", organization=org).exists()

    def test_invite_creates_pending_status(self, owner_client, org):
        owner_client.post(
            "/api/v1/auth/invite/",
            {"email": "t@test.com", "role": "tenant"},
            content_type="application/json",
        )
        invite = Invite.objects.get(email="t@test.com", organization=org)
        assert invite.status == Invite.Status.PENDING

    def test_cannot_invite_as_owner(self, owner_client):
        resp = owner_client.post(
            "/api/v1/auth/invite/",
            {"email": "bad@test.com", "role": "owner"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_duplicate_pending_invite_blocked(self, owner_client, org):
        owner_client.post(
            "/api/v1/auth/invite/",
            {"email": "dup@test.com", "role": "tenant"},
            content_type="application/json",
        )
        resp = owner_client.post(
            "/api/v1/auth/invite/",
            {"email": "dup@test.com", "role": "tenant"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "pending invite" in resp.data["detail"].lower()

    def test_non_owner_cannot_invite(self, client, org):
        tenant = User.objects.create_user(email="t@test.com", password="pass1234567")
        Membership.objects.create(user=tenant, organization=org, role=Membership.Role.TENANT)
        tenant.active_organization = org
        tenant.save(update_fields=["active_organization"])
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(tenant)
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token.access_token}"
        resp = client.post(
            "/api/v1/auth/invite/",
            {"email": "x@test.com", "role": "tenant"},
            content_type="application/json",
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestValidateInvite:
    def test_valid_token_returns_invite_info(self, client, org, owner):
        invite = Invite.objects.create(
            organization=org, invited_by=owner, email="t@test.com", role="tenant"
        )
        resp = client.get(f"/api/v1/auth/invite/{invite.token}/")
        assert resp.status_code == 200
        assert resp.data["email"] == "t@test.com"
        assert resp.data["role"] == "tenant"
        assert resp.data["organization"] == org.name

    def test_invalid_token_returns_404(self, client):
        resp = client.get("/api/v1/auth/invite/notarealtoken/")
        assert resp.status_code == 404

    def test_expired_invite_returns_404(self, client, org, owner):
        from datetime import timedelta
        invite = Invite(
            organization=org, invited_by=owner, email="e@test.com", role="tenant",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        invite.save()
        resp = client.get(f"/api/v1/auth/invite/{invite.token}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAcceptInvite:
    def test_new_user_can_accept_invite(self, client, org, owner):
        invite = Invite.objects.create(
            organization=org, invited_by=owner, email="brand@test.com", role="tenant"
        )
        resp = client.post(
            "/api/v1/auth/accept-invite/",
            {
                "token": invite.token,
                "first_name": "Brand",
                "last_name": "New",
                "password": "strongpassword1",
            },
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert "access" in resp.data
        user = User.objects.get(email="brand@test.com")
        assert user.email_verified is True
        assert Membership.objects.filter(user=user, organization=org, role="tenant").exists()
        invite.refresh_from_db()
        assert invite.status == Invite.Status.ACCEPTED

    def test_existing_user_can_accept_invite(self, client, org, owner):
        existing = User.objects.create_user(email="existing@test.com", password="strongpassword1")
        invite = Invite.objects.create(
            organization=org, invited_by=owner, email="existing@test.com", role="tenant"
        )
        resp = client.post(
            "/api/v1/auth/accept-invite/",
            {"token": invite.token},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert Membership.objects.filter(user=existing, organization=org).exists()

    def test_invalid_token_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/accept-invite/",
            {"token": "bogus", "password": "strongpassword1"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_password_required_for_new_user(self, client, org, owner):
        invite = Invite.objects.create(
            organization=org, invited_by=owner, email="np@test.com", role="tenant"
        )
        resp = client.post(
            "/api/v1/auth/accept-invite/",
            {"token": invite.token, "first_name": "No"},
            content_type="application/json",
        )
        assert resp.status_code == 400
