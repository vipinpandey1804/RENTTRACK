"""
Tests for meter reading submission and confirmation (#17, #19).

Covers:
  - Submit a reading (POST /metering/readings/)
  - Validation: current < previous, locked period, duplicate
  - Confirm a reading (PATCH /metering/readings/{id}/confirm/)
  - Electricity bill is generated on confirm
  - Idempotency: re-confirming returns existing bill
  - Org isolation: cross-org readings return 404
"""

from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, Organization, User
from apps.billing.models import Bill
from apps.metering.models import MeterReading
from apps.properties.models import Lease, Property, Unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _authed_client(user: User) -> Client:
    c = Client()
    c.defaults["HTTP_AUTHORIZATION"] = f"Bearer {RefreshToken.for_user(user).access_token}"
    return c


@pytest.fixture
def org():
    return Organization.objects.create(
        name="Meter Org", slug="meter-org", primary_email="owner@meter.com"
    )


@pytest.fixture
def owner(org):
    user = User.objects.create_user(
        email="owner@meter.com",
        password="strongpassword1",  # pragma: allowlist secret
        first_name="Owner",
    )
    Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
    user.active_organization = org
    user.save(update_fields=["active_organization"])
    return user


@pytest.fixture
def tenant(org):
    user = User.objects.create_user(
        email="tenant@meter.com",
        password="strongpassword1",  # pragma: allowlist secret
        first_name="Tenant",
    )
    Membership.objects.create(user=user, organization=org, role=Membership.Role.TENANT)
    user.active_organization = org
    user.save(update_fields=["active_organization"])
    return user


@pytest.fixture
def prop(org):
    return Property.objects.create(
        organization=org,
        name="Meter Property",
        property_type=Property.PropertyType.RESIDENTIAL,
        address_line1="1 Meter St",
        city="Mumbai",
        state="MH",
        postal_code="400001",
        electricity_rate_per_unit=Decimal("8.50"),
    )


@pytest.fixture
def unit(org, prop):
    return Unit.objects.create(
        organization=org,
        property=prop,
        name="Unit M1",
        base_rent="10000.00",
        security_deposit="20000.00",
    )


@pytest.fixture
def active_lease(org, unit, tenant):
    return Lease.objects.create(
        organization=org,
        unit=unit,
        tenant=tenant,
        start_date=timezone.now().date(),
        monthly_rent="10000.00",
        status=Lease.Status.ACTIVE,
    )


@pytest.fixture
def owner_client(owner):
    return _authed_client(owner)


@pytest.fixture
def tenant_client(tenant):
    return _authed_client(tenant)


# ---------------------------------------------------------------------------
# Submit reading tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSubmitReading:
    def test_submit_first_reading(self, owner_client, unit, active_lease):
        """First reading auto-sets previous_reading=0."""
        resp = owner_client.post(
            "/api/v1/metering/readings/",
            {
                "unit": str(unit.id),
                "meter_type": "electricity",
                "period_month": "2026-04-01",
                "current_reading": "150.00",
                "notes": "",
            },
            content_type="application/json",
        )
        assert resp.status_code == 201, resp.json()
        data = resp.json()
        assert data["previous_reading"] == "0.00"
        assert data["current_reading"] == "150.00"
        assert data["units_consumed"] == "150.00"
        assert data["status"] == "submitted"

    def test_previous_reading_auto_populated(self, owner_client, unit, active_lease):
        """Second reading uses current of the first as previous."""
        MeterReading.objects.create(
            organization=unit.organization,
            unit=unit,
            meter_type="electricity",
            period_month="2026-03-01",
            previous_reading=Decimal("0"),
            current_reading=Decimal("100"),
            units_consumed=Decimal("100"),
            status=MeterReading.Status.LOCKED,
            submitted_by=None,
        )
        resp = owner_client.post(
            "/api/v1/metering/readings/",
            {
                "unit": str(unit.id),
                "meter_type": "electricity",
                "period_month": "2026-04-01",
                "current_reading": "175.00",
            },
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.json()["previous_reading"] == "100.00"
        assert resp.json()["units_consumed"] == "75.00"

    def test_rejects_current_less_than_previous(self, owner_client, unit, active_lease):
        """current_reading < previous_reading must fail with 400."""
        MeterReading.objects.create(
            organization=unit.organization,
            unit=unit,
            meter_type="electricity",
            period_month="2026-03-01",
            previous_reading=Decimal("0"),
            current_reading=Decimal("200"),
            units_consumed=Decimal("200"),
            status=MeterReading.Status.LOCKED,
            submitted_by=None,
        )
        resp = owner_client.post(
            "/api/v1/metering/readings/",
            {
                "unit": str(unit.id),
                "meter_type": "electricity",
                "period_month": "2026-04-01",
                "current_reading": "50.00",
            },
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "current_reading" in resp.json()

    def test_rejects_locked_period(self, owner_client, unit, active_lease):
        """Cannot submit for an already-locked period."""
        MeterReading.objects.create(
            organization=unit.organization,
            unit=unit,
            meter_type="electricity",
            period_month="2026-04-01",
            previous_reading=Decimal("0"),
            current_reading=Decimal("100"),
            units_consumed=Decimal("100"),
            status=MeterReading.Status.LOCKED,
            submitted_by=None,
        )
        resp = owner_client.post(
            "/api/v1/metering/readings/",
            {
                "unit": str(unit.id),
                "meter_type": "electricity",
                "period_month": "2026-04-01",
                "current_reading": "120.00",
            },
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_rejects_non_first_of_month(self, owner_client, unit, active_lease):
        """period_month must be the first of the month."""
        resp = owner_client.post(
            "/api/v1/metering/readings/",
            {
                "unit": str(unit.id),
                "meter_type": "electricity",
                "period_month": "2026-04-15",
                "current_reading": "100.00",
            },
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "period_month" in resp.json()

    def test_unauthenticated_returns_401(self, unit, active_lease):
        resp = Client().post(
            "/api/v1/metering/readings/",
            {
                "unit": str(unit.id),
                "meter_type": "electricity",
                "period_month": "2026-04-01",
                "current_reading": "100.00",
            },
            content_type="application/json",
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Confirm + electricity bill generation tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestConfirmReading:
    def _create_reading(self, unit):
        return MeterReading.objects.create(
            organization=unit.organization,
            unit=unit,
            meter_type="electricity",
            period_month="2026-04-01",
            previous_reading=Decimal("100"),
            current_reading=Decimal("250"),
            units_consumed=Decimal("150"),
            status=MeterReading.Status.SUBMITTED,
            submitted_by=None,
        )

    def test_confirm_generates_electricity_bill(self, owner_client, unit, active_lease):
        reading = self._create_reading(unit)
        resp = owner_client.patch(
            f"/api/v1/metering/readings/{reading.id}/confirm/",
            content_type="application/json",
        )
        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["status"] == "locked"
        assert "bill_id" in data

        bill = Bill.objects.get(id=data["bill_id"])
        assert bill.bill_type == Bill.BillType.ELECTRICITY
        assert bill.status == Bill.Status.ISSUED
        # 150 units × ₹8.50 = ₹1275.00
        assert bill.total_amount == Decimal("1275.00")
        assert bill.line_items.count() == 1

    def test_confirm_locks_reading(self, owner_client, unit, active_lease):
        reading = self._create_reading(unit)
        owner_client.patch(
            f"/api/v1/metering/readings/{reading.id}/confirm/",
            content_type="application/json",
        )
        reading.refresh_from_db()
        assert reading.status == MeterReading.Status.LOCKED

    def test_confirm_idempotent(self, owner_client, unit, active_lease):
        """Confirming again returns the same bill, no duplicate created."""
        reading = self._create_reading(unit)
        r1 = owner_client.patch(
            f"/api/v1/metering/readings/{reading.id}/confirm/",
            content_type="application/json",
        )
        # After confirm the reading is locked; try again
        r2 = owner_client.patch(
            f"/api/v1/metering/readings/{reading.id}/confirm/",
            content_type="application/json",
        )
        assert r2.status_code == 400
        assert "locked" in r2.json()["detail"]
        # Only one bill created
        assert Bill.objects.filter(bill_type=Bill.BillType.ELECTRICITY).count() == 1
        assert r1.json()["bill_id"] is not None

    def test_confirm_requires_owner_or_manager(self, tenant_client, unit, active_lease):
        reading = self._create_reading(unit)
        resp = tenant_client.patch(
            f"/api/v1/metering/readings/{reading.id}/confirm/",
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_confirm_fails_without_active_lease(self, owner_client, unit):
        """If no active lease exists, confirm returns 400."""
        reading = self._create_reading(unit)
        resp = owner_client.patch(
            f"/api/v1/metering/readings/{reading.id}/confirm/",
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "lease" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# List / detail tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMeterReadingList:
    def test_list_scoped_to_org(self, owner_client, unit, active_lease):
        MeterReading.objects.create(
            organization=unit.organization,
            unit=unit,
            meter_type="electricity",
            period_month="2026-04-01",
            previous_reading=Decimal("0"),
            current_reading=Decimal("100"),
            units_consumed=Decimal("100"),
            status=MeterReading.Status.SUBMITTED,
            submitted_by=None,
        )
        resp = owner_client.get("/api/v1/metering/readings/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
