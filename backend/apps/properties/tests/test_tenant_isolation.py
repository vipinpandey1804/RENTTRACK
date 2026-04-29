"""
Tenant isolation integration tests.

For every tenant-scoped model (Property, Unit, Lease, Bill, Payment):
  1. Create data in Org A and Org B.
  2. Authenticate as Org A owner → Org B data is invisible (404 on detail, absent from list).
  3. Authenticate as Org B owner → Org A data is invisible.
"""

import pytest
from django.test import Client
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, Organization, User
from apps.billing.models import Bill, BillLineItem
from apps.payments.models import Payment
from apps.properties.models import Lease, Property, Unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_org(slug: str) -> Organization:
    return Organization.objects.create(
        name=f"Org {slug}",
        slug=slug,
        primary_email=f"owner@{slug}.com",
    )


def _make_owner(org: Organization) -> User:
    user = User.objects.create_user(
        email=f"owner@{org.slug}.com",
        password="strongpassword1",  # pragma: allowlist secret
        first_name="Owner",
    )
    Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
    user.active_organization = org
    user.save(update_fields=["active_organization"])
    return user


def _authed_client(user: User) -> Client:
    c = Client()
    token = RefreshToken.for_user(user).access_token
    c.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return c


# ---------------------------------------------------------------------------
# Fixtures: two orgs, two owners, two authed clients
# ---------------------------------------------------------------------------


@pytest.fixture
def org_a():
    return _make_org("isolation-a")


@pytest.fixture
def org_b():
    return _make_org("isolation-b")


@pytest.fixture
def owner_a(org_a):
    return _make_owner(org_a)


@pytest.fixture
def owner_b(org_b):
    return _make_owner(org_b)


@pytest.fixture
def client_a(owner_a):
    return _authed_client(owner_a)


@pytest.fixture
def client_b(owner_b):
    return _authed_client(owner_b)


# ---------------------------------------------------------------------------
# Fixtures: one property/unit/lease/bill/payment per org
# ---------------------------------------------------------------------------


@pytest.fixture
def property_a(org_a):
    return Property.objects.create(
        organization=org_a,
        name="Property A",
        property_type=Property.PropertyType.RESIDENTIAL,
        address_line1="1 Alpha Street",
        city="Mumbai",
        state="MH",
        postal_code="400001",
    )


@pytest.fixture
def property_b(org_b):
    return Property.objects.create(
        organization=org_b,
        name="Property B",
        property_type=Property.PropertyType.RESIDENTIAL,
        address_line1="2 Beta Street",
        city="Delhi",
        state="DL",
        postal_code="110001",
    )


@pytest.fixture
def unit_a(org_a, property_a):
    return Unit.objects.create(
        organization=org_a,
        property=property_a,
        name="Unit A1",
        base_rent="10000.00",
        security_deposit="20000.00",
    )


@pytest.fixture
def unit_b(org_b, property_b):
    return Unit.objects.create(
        organization=org_b,
        property=property_b,
        name="Unit B1",
        base_rent="15000.00",
        security_deposit="30000.00",
    )


@pytest.fixture
def tenant_a(org_a):
    user = User.objects.create_user(
        email="tenant@isolation-a.com",
        password="strongpassword1",
        first_name="Tenant",
    )
    Membership.objects.create(user=user, organization=org_a, role=Membership.Role.TENANT)
    user.active_organization = org_a
    user.save(update_fields=["active_organization"])
    return user


@pytest.fixture
def tenant_b(org_b):
    user = User.objects.create_user(
        email="tenant@isolation-b.com",
        password="strongpassword1",
        first_name="Tenant",
    )
    Membership.objects.create(user=user, organization=org_b, role=Membership.Role.TENANT)
    user.active_organization = org_b
    user.save(update_fields=["active_organization"])
    return user


@pytest.fixture
def lease_a(org_a, unit_a, tenant_a):
    return Lease.objects.create(
        organization=org_a,
        unit=unit_a,
        tenant=tenant_a,
        start_date=timezone.now().date(),
        monthly_rent="10000.00",
        status=Lease.Status.ACTIVE,
    )


@pytest.fixture
def lease_b(org_b, unit_b, tenant_b):
    return Lease.objects.create(
        organization=org_b,
        unit=unit_b,
        tenant=tenant_b,
        start_date=timezone.now().date(),
        monthly_rent="15000.00",
        status=Lease.Status.ACTIVE,
    )


def _make_bill(org, lease, number):
    today = timezone.now().date()
    bill = Bill.objects.create(
        organization=org,
        lease=lease,
        bill_number=number,
        bill_type=Bill.BillType.RENT,
        period_start=today.replace(day=1),
        period_end=today,
        issue_date=today,
        due_date=today,
        total_amount="10000.00",
    )
    BillLineItem.objects.create(
        organization=org,
        bill=bill,
        description="Rent",
        unit_price="10000.0000",
        amount="10000.00",
    )
    return bill


@pytest.fixture
def bill_a(org_a, lease_a):
    return _make_bill(org_a, lease_a, "ISO-BILL-A-001")


@pytest.fixture
def bill_b(org_b, lease_b):
    return _make_bill(org_b, lease_b, "ISO-BILL-B-001")


@pytest.fixture
def payment_a(org_a, bill_a):
    return Payment.objects.create(
        organization=org_a,
        bill=bill_a,
        amount="10000.00",
        method=Payment.Method.BANK_TRANSFER,
        status=Payment.Status.SUCCESS,
    )


@pytest.fixture
def payment_b(org_b, bill_b):
    return Payment.objects.create(
        organization=org_b,
        bill=bill_b,
        amount="10000.00",
        method=Payment.Method.BANK_TRANSFER,
        status=Payment.Status.SUCCESS,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPropertyIsolation:
    def test_list_shows_only_own_org(self, client_a, client_b, property_a, property_b):
        resp = client_a.get("/api/v1/properties/")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(property_a.id) in ids
        assert str(property_b.id) not in ids

        resp = client_b.get("/api/v1/properties/")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(property_b.id) in ids
        assert str(property_a.id) not in ids

    def test_detail_cross_org_returns_404(self, client_a, client_b, property_a, property_b):
        assert client_a.get(f"/api/v1/properties/{property_b.id}/").status_code == 404
        assert client_b.get(f"/api/v1/properties/{property_a.id}/").status_code == 404


@pytest.mark.django_db
class TestUnitIsolation:
    def test_list_shows_only_own_org(self, client_a, client_b, unit_a, unit_b):
        resp = client_a.get("/api/v1/properties/units/")
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()["results"]]
        assert str(unit_a.id) in ids
        assert str(unit_b.id) not in ids

        resp = client_b.get("/api/v1/properties/units/")
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()["results"]]
        assert str(unit_b.id) in ids
        assert str(unit_a.id) not in ids

    def test_detail_cross_org_returns_404(self, client_a, client_b, unit_a, unit_b):
        assert client_a.get(f"/api/v1/properties/units/{unit_b.id}/").status_code == 404
        assert client_b.get(f"/api/v1/properties/units/{unit_a.id}/").status_code == 404


@pytest.mark.django_db
class TestLeaseIsolation:
    def test_list_shows_only_own_org(self, client_a, client_b, lease_a, lease_b):
        resp = client_a.get("/api/v1/properties/leases/")
        assert resp.status_code == 200
        ids = [le["id"] for le in resp.json()["results"]]
        assert str(lease_a.id) in ids
        assert str(lease_b.id) not in ids

        resp = client_b.get("/api/v1/properties/leases/")
        assert resp.status_code == 200
        ids = [le["id"] for le in resp.json()["results"]]
        assert str(lease_b.id) in ids
        assert str(lease_a.id) not in ids

    def test_detail_cross_org_returns_404(self, client_a, client_b, lease_a, lease_b):
        assert client_a.get(f"/api/v1/properties/leases/{lease_b.id}/").status_code == 404
        assert client_b.get(f"/api/v1/properties/leases/{lease_a.id}/").status_code == 404


@pytest.mark.django_db
class TestBillIsolation:
    def test_list_shows_only_own_org(self, client_a, client_b, bill_a, bill_b):
        resp = client_a.get("/api/v1/billing/bills/")
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.json()["results"]]
        assert str(bill_a.id) in ids
        assert str(bill_b.id) not in ids

        resp = client_b.get("/api/v1/billing/bills/")
        assert resp.status_code == 200
        ids = [b["id"] for b in resp.json()["results"]]
        assert str(bill_b.id) in ids
        assert str(bill_a.id) not in ids

    def test_detail_cross_org_returns_404(self, client_a, client_b, bill_a, bill_b):
        assert client_a.get(f"/api/v1/billing/bills/{bill_b.id}/").status_code == 404
        assert client_b.get(f"/api/v1/billing/bills/{bill_a.id}/").status_code == 404


@pytest.mark.django_db
class TestPaymentIsolation:
    def test_list_shows_only_own_org(self, client_a, client_b, payment_a, payment_b):
        resp = client_a.get("/api/v1/payments/")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(payment_a.id) in ids
        assert str(payment_b.id) not in ids

        resp = client_b.get("/api/v1/payments/")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(payment_b.id) in ids
        assert str(payment_a.id) not in ids

    def test_detail_cross_org_returns_404(self, client_a, client_b, payment_a, payment_b):
        assert client_a.get(f"/api/v1/payments/{payment_b.id}/").status_code == 404
        assert client_b.get(f"/api/v1/payments/{payment_a.id}/").status_code == 404
