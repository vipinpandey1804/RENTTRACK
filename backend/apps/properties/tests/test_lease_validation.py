"""Tests for overlapping lease validation (Issue #13)."""
import pytest

from apps.accounts.models import Membership, Organization, User
from apps.properties.models import Lease, Property, Unit


@pytest.fixture
def org():
    return Organization.objects.create(
        name="Lease Test Org", slug="lease-test-org", primary_email="o@test.com"
    )


@pytest.fixture
def owner(org):
    user = User.objects.create_user(email="o@test.com", password="strongpassword1")
    Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
    user.active_organization = org
    user.save(update_fields=["active_organization"])
    return user


@pytest.fixture
def owner_client(client, owner):
    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(owner)
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token.access_token}"
    return client


@pytest.fixture
def prop(org):
    return Property.objects.create(
        organization=org,
        name="Test Building",
        address_line1="1 Test St",
        city="Mumbai",
        state="MH",
        postal_code="400001",
    )


@pytest.fixture
def unit(prop, org):
    return Unit.objects.create(
        organization=org, property=prop, name="Flat 1A", base_rent=10000
    )


@pytest.fixture
def tenant(org):
    user = User.objects.create_user(email="tenant@test.com", password="strongpassword1")
    Membership.objects.create(user=user, organization=org, role=Membership.Role.TENANT)
    return user


@pytest.mark.django_db
class TestOverlappingLeaseValidation:
    def _create_active_lease(self, unit, tenant, org):
        lease = Lease.objects.create(
            organization=org,
            unit=unit,
            tenant=tenant,
            start_date="2026-01-01",
            monthly_rent=10000,
            status=Lease.Status.ACTIVE,
        )
        unit.status = Unit.Status.OCCUPIED
        unit.save(update_fields=["status"])
        return lease

    def test_can_activate_draft_lease_on_vacant_unit(self, owner_client, unit, tenant, org):
        lease = Lease.objects.create(
            organization=org, unit=unit, tenant=tenant,
            start_date="2026-04-01", monthly_rent=10000,
            status=Lease.Status.DRAFT,
        )
        resp = owner_client.post(f"/api/v1/properties/leases/{lease.id}/activate/")
        assert resp.status_code == 200
        assert resp.data["status"] == "active"

    def test_activating_lease_on_occupied_unit_is_blocked(
        self, owner_client, unit, tenant, org
    ):
        tenant2 = User.objects.create_user(email="t2@test.com", password="strongpassword1")
        Membership.objects.create(user=tenant2, organization=org, role=Membership.Role.TENANT)

        # First lease is already active
        self._create_active_lease(unit, tenant, org)

        # Second draft lease for same unit
        draft_lease = Lease.objects.create(
            organization=org, unit=unit, tenant=tenant2,
            start_date="2026-04-01", monthly_rent=10000,
            status=Lease.Status.DRAFT,
        )
        resp = owner_client.post(f"/api/v1/properties/leases/{draft_lease.id}/activate/")
        assert resp.status_code == 400
        assert "active lease" in resp.data["detail"].lower()

    def test_activation_blocked_message_includes_tenant_email(
        self, owner_client, unit, tenant, org
    ):
        tenant2 = User.objects.create_user(email="t2@test.com", password="strongpassword1")
        Membership.objects.create(user=tenant2, organization=org, role=Membership.Role.TENANT)
        self._create_active_lease(unit, tenant, org)
        draft_lease = Lease.objects.create(
            organization=org, unit=unit, tenant=tenant2,
            start_date="2026-04-01", monthly_rent=10000,
            status=Lease.Status.DRAFT,
        )
        resp = owner_client.post(f"/api/v1/properties/leases/{draft_lease.id}/activate/")
        assert "tenant@test.com" in resp.data["detail"]

    def test_only_active_leases_block_activation(self, owner_client, unit, tenant, org):
        tenant2 = User.objects.create_user(email="t2@test.com", password="strongpassword1")
        Membership.objects.create(user=tenant2, organization=org, role=Membership.Role.TENANT)

        # Ended lease on same unit — should NOT block
        Lease.objects.create(
            organization=org, unit=unit, tenant=tenant,
            start_date="2025-01-01", monthly_rent=10000,
            status=Lease.Status.ENDED,
        )
        draft_lease = Lease.objects.create(
            organization=org, unit=unit, tenant=tenant2,
            start_date="2026-04-01", monthly_rent=10000,
            status=Lease.Status.DRAFT,
        )
        resp = owner_client.post(f"/api/v1/properties/leases/{draft_lease.id}/activate/")
        assert resp.status_code == 200

    def test_activating_already_active_lease_returns_400(
        self, owner_client, unit, tenant, org
    ):
        lease = self._create_active_lease(unit, tenant, org)
        resp = owner_client.post(f"/api/v1/properties/leases/{lease.id}/activate/")
        assert resp.status_code == 400
        assert "only draft leases" in resp.data["detail"].lower()
