"""Tests for bill PDF generation (#15)."""

import os
import tempfile
from datetime import date

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, Organization, User
from apps.billing.models import Bill, BillLineItem
from apps.billing.pdf import generate_bill_pdf
from apps.billing.tasks import generate_bill_pdf_task
from apps.properties.models import Lease, Property, Unit

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def org():
    return Organization.objects.create(
        name="PDF Test Org", slug="pdf-test-org", primary_email="owner@pdf.com"
    )


@pytest.fixture
def owner(org):
    u = User.objects.create_user(
        email="owner@pdf.com",
        password="strongpassword1",  # pragma: allowlist secret
        first_name="Alice",
        last_name="Owner",
    )
    Membership.objects.create(user=u, organization=org, role=Membership.Role.OWNER)
    u.active_organization = org
    u.save(update_fields=["active_organization"])
    return u


@pytest.fixture
def tenant(org):
    return User.objects.create_user(
        email="tenant@pdf.com",
        password="strongpassword1",  # pragma: allowlist secret
        first_name="Bob",
        last_name="Tenant",
    )


@pytest.fixture
def lease(org, tenant):
    prop = Property.objects.create(
        organization=org,
        name="PDF Property",
        address_line1="10 Main St",
        city="Mumbai",
        state="MH",
        postal_code="400001",
    )
    unit = Unit.objects.create(organization=org, property=prop, name="Unit A", base_rent=15000)
    return Lease.objects.create(
        organization=org,
        unit=unit,
        tenant=tenant,
        start_date=date(2026, 1, 1),
        monthly_rent=15000,
        status=Lease.Status.ACTIVE,
    )


@pytest.fixture
def bill(org, lease):
    b = Bill.objects.create(
        organization=org,
        lease=lease,
        bill_number="RT-202604-PDF-ABC123",
        bill_type=Bill.BillType.RENT,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        issue_date=timezone.now().date(),
        due_date=date(2026, 4, 28),
        subtotal=15000,
        tax_amount=0,
        total_amount=15000,
        amount_paid=0,
        status=Bill.Status.ISSUED,
    )
    BillLineItem.objects.create(
        organization=org,
        bill=b,
        description="Rent – April 2026",
        quantity=1,
        unit_price=15000,
        amount=15000,
    )
    return b


def _authed_client(user):
    from django.test import Client

    c = Client()
    c.defaults["HTTP_AUTHORIZATION"] = f"Bearer {RefreshToken.for_user(user).access_token}"
    return c


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGenerateBillPdf:
    def test_returns_bytes(self, bill):
        pdf_bytes = generate_bill_pdf(bill)
        assert isinstance(pdf_bytes, bytes)

    def test_starts_with_pdf_header(self, bill):
        pdf_bytes = generate_bill_pdf(bill)
        assert pdf_bytes[:4] == b"%PDF"

    def test_non_empty(self, bill):
        pdf_bytes = generate_bill_pdf(bill)
        assert len(pdf_bytes) > 1024


@pytest.mark.django_db
class TestGenerateBillPdfTask:
    def test_task_writes_file_and_updates_pdf_url(self, bill):
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir, MEDIA_URL="/media/"):
                generate_bill_pdf_task(str(bill.id))

                expected_path = os.path.join(tmpdir, "bills", f"{bill.id}.pdf")
                assert os.path.exists(expected_path)
                assert os.path.getsize(expected_path) > 1024

                bill.refresh_from_db()
                assert bill.pdf_url == f"/media/bills/{bill.id}.pdf"

    def test_task_is_idempotent(self, bill):
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir, MEDIA_URL="/media/"):
                generate_bill_pdf_task(str(bill.id))
                generate_bill_pdf_task(str(bill.id))

                bill.refresh_from_db()
                assert bill.pdf_url == f"/media/bills/{bill.id}.pdf"


@pytest.mark.django_db
class TestPdfEndpoint:
    def test_returns_202_when_pdf_not_yet_generated(self, owner, bill):
        client = _authed_client(owner)
        resp = client.get(f"/api/v1/billing/bills/{bill.id}/pdf/")
        assert resp.status_code == 202

    def test_returns_pdf_file_when_generated(self, owner, bill):
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir, MEDIA_URL="/media/"):
                generate_bill_pdf_task(str(bill.id))

                client = _authed_client(owner)
                resp = client.get(f"/api/v1/billing/bills/{bill.id}/pdf/")
                assert resp.status_code == 200
                assert resp["Content-Type"] == "application/pdf"
                assert f"{bill.bill_number}.pdf" in resp["Content-Disposition"]

    def test_unauthenticated_returns_401(self, bill):
        from django.test import Client

        resp = Client().get(f"/api/v1/billing/bills/{bill.id}/pdf/")
        assert resp.status_code == 401
