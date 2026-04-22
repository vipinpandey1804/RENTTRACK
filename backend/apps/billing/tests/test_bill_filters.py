"""Tests for billing API filters and date range (Issue #16 backend)."""
import pytest
from django.utils import timezone

from apps.accounts.models import Membership, Organization, User
from apps.billing.models import Bill, BillLineItem
from apps.properties.models import Lease, Property, Unit


@pytest.fixture
def org():
    return Organization.objects.create(
        name="Billing Test Org", slug="billing-test-org", primary_email="o@billing.com"
    )


@pytest.fixture
def owner(org):
    user = User.objects.create_user(email="o@billing.com", password="strongpassword1")
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
def tenant(org):
    user = User.objects.create_user(email="tenant@billing.com", password="strongpassword1")
    Membership.objects.create(user=user, organization=org, role=Membership.Role.TENANT)
    return user


@pytest.fixture
def lease(org, tenant):
    prop = Property.objects.create(
        organization=org, name="Billing Prop",
        address_line1="1 St", city="Mumbai", state="MH", postal_code="400001",
    )
    unit = Unit.objects.create(
        organization=org, property=prop, name="Unit 1", base_rent=10000
    )
    return Lease.objects.create(
        organization=org, unit=unit, tenant=tenant,
        start_date="2026-01-01", monthly_rent=10000, status=Lease.Status.ACTIVE,
    )


def make_bill(org, lease, bill_number, due_date, status=Bill.Status.ISSUED):
    bill = Bill.objects.create(
        organization=org,
        lease=lease,
        bill_number=bill_number,
        bill_type=Bill.BillType.RENT,
        period_start="2026-04-01",
        period_end="2026-04-30",
        issue_date="2026-04-01",
        due_date=due_date,
        subtotal="10000.00",
        total_amount="10000.00",
        status=status,
    )
    BillLineItem.objects.create(
        organization=org,
        bill=bill,
        description="Rent",
        quantity=1,
        unit_price="10000.00",
        amount="10000.00",
    )
    return bill


@pytest.mark.django_db
class TestBillListFilters:
    def test_list_all_bills(self, owner_client, org, lease):
        make_bill(org, lease, "RT-0001", "2026-04-10")
        make_bill(org, lease, "RT-0002", "2026-05-10", Bill.Status.PAID)
        resp = owner_client.get("/api/v1/billing/bills/")
        assert resp.status_code == 200
        assert resp.data["count"] == 2

    def test_filter_by_status(self, owner_client, org, lease):
        make_bill(org, lease, "RT-0001", "2026-04-10", Bill.Status.ISSUED)
        make_bill(org, lease, "RT-0002", "2026-05-10", Bill.Status.PAID)
        resp = owner_client.get("/api/v1/billing/bills/?status=issued")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["bill_number"] == "RT-0001"

    def test_filter_due_date_gte(self, owner_client, org, lease):
        make_bill(org, lease, "RT-EARLY", "2026-03-01")
        make_bill(org, lease, "RT-LATE", "2026-05-01")
        resp = owner_client.get("/api/v1/billing/bills/?due_date__gte=2026-04-01")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["bill_number"] == "RT-LATE"

    def test_filter_due_date_lte(self, owner_client, org, lease):
        make_bill(org, lease, "RT-EARLY", "2026-03-01")
        make_bill(org, lease, "RT-LATE", "2026-05-01")
        resp = owner_client.get("/api/v1/billing/bills/?due_date__lte=2026-04-01")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["bill_number"] == "RT-EARLY"

    def test_filter_due_date_range(self, owner_client, org, lease):
        make_bill(org, lease, "RT-JAN", "2026-01-10")
        make_bill(org, lease, "RT-APR", "2026-04-10")
        make_bill(org, lease, "RT-JUL", "2026-07-10")
        resp = owner_client.get(
            "/api/v1/billing/bills/?due_date__gte=2026-03-01&due_date__lte=2026-05-01"
        )
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["bill_number"] == "RT-APR"

    def test_search_by_bill_number(self, owner_client, org, lease):
        make_bill(org, lease, "RT-SEARCH-001", "2026-04-10")
        make_bill(org, lease, "RT-OTHER-002", "2026-04-10")
        resp = owner_client.get("/api/v1/billing/bills/?search=SEARCH")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["bill_number"] == "RT-SEARCH-001"

    def test_unauthenticated_request_returns_401(self, client):
        resp = client.get("/api/v1/billing/bills/")
        assert resp.status_code == 401

    def test_org_isolation(self, owner_client, org, lease):
        # Bill from a different org should not appear
        other_org = Organization.objects.create(
            name="Other Org", slug="other-org", primary_email="x@other.com"
        )
        other_user = User.objects.create_user(email="x@other.com", password="strongpassword1")
        Membership.objects.create(user=other_user, organization=other_org, role=Membership.Role.OWNER)
        other_prop = Property.objects.create(
            organization=other_org, name="Other Prop",
            address_line1="2 St", city="Delhi", state="DL", postal_code="110001",
        )
        other_unit = Unit.objects.create(
            organization=other_org, property=other_prop, name="U1", base_rent=5000
        )
        other_tenant = User.objects.create_user(email="ot@other.com", password="strongpassword1")
        other_lease = Lease.objects.create(
            organization=other_org, unit=other_unit, tenant=other_tenant,
            start_date="2026-01-01", monthly_rent=5000, status=Lease.Status.ACTIVE,
        )
        make_bill(other_org, other_lease, "OTHER-001", "2026-04-10")
        # Our org has no bills
        resp = owner_client.get("/api/v1/billing/bills/")
        assert resp.data["count"] == 0
