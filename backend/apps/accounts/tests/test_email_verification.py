"""Tests for email verification flow (Issue #5)."""

import pytest
from django.core.cache import cache

from apps.accounts.models import User


@pytest.mark.django_db
class TestEmailVerification:
    def test_signup_creates_unverified_user(self, client):
        resp = client.post(
            "/api/v1/auth/signup/",
            {
                "email": "newuser@test.com",
                "password": "strongpassword1",
                "first_name": "New",
                "org_name": "New Org",
            },
            content_type="application/json",
        )
        assert resp.status_code == 201
        user = User.objects.get(email="newuser@test.com")
        assert user.email_verified is False

    def test_verify_email_with_valid_token(self, client):
        user = User.objects.create_user(email="v@test.com", password="pass1234567")
        import secrets

        token = secrets.token_urlsafe(32)
        cache.set(f"email_verification:{token}", str(user.id), 86400)

        resp = client.post(
            "/api/v1/auth/verify-email/",
            {"token": token},
            content_type="application/json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.email_verified is True

    def test_verify_email_with_invalid_token(self, client):
        resp = client.post(
            "/api/v1/auth/verify-email/",
            {"token": "totally-invalid-token"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Invalid or expired" in resp.data["detail"]

    def test_verify_email_token_consumed_after_use(self, client):
        user = User.objects.create_user(email="once@test.com", password="pass1234567")
        import secrets

        token = secrets.token_urlsafe(32)
        cache.set(f"email_verification:{token}", str(user.id), 86400)

        client.post("/api/v1/auth/verify-email/", {"token": token}, content_type="application/json")
        # Second use must fail
        resp = client.post(
            "/api/v1/auth/verify-email/", {"token": token}, content_type="application/json"
        )
        assert resp.status_code == 400

    def test_resend_verification_requires_auth(self, client):
        resp = client.post("/api/v1/auth/resend-verification/")
        assert resp.status_code == 401

    def test_resend_verification_for_unverified_user(self, owner_client, owner):
        owner.email_verified = False
        owner.save(update_fields=["email_verified"])
        resp = owner_client.post("/api/v1/auth/resend-verification/")
        assert resp.status_code == 200

    def test_resend_verification_for_already_verified_user(self, owner_client, owner):
        owner.email_verified = True
        owner.save(update_fields=["email_verified"])
        resp = owner_client.post("/api/v1/auth/resend-verification/")
        assert resp.status_code == 400
        assert "already verified" in resp.data["detail"]

    def test_verify_email_missing_token(self, client):
        resp = client.post("/api/v1/auth/verify-email/", {}, content_type="application/json")
        assert resp.status_code == 400
