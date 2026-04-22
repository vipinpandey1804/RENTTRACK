"""Shared fixtures for accounts tests."""
import pytest
from django.utils.text import slugify

from apps.accounts.models import Membership, Organization, User


@pytest.fixture
def org():
    return Organization.objects.create(
        name="Test Org",
        slug="test-org",
        primary_email="owner@test.com",
    )


@pytest.fixture
def owner(org):
    user = User.objects.create_user(
        email="owner@test.com",
        password="strongpassword1",
        first_name="Owner",
    )
    Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
    user.active_organization = org
    user.save(update_fields=["active_organization"])
    return user


@pytest.fixture
def owner_client(client, owner):
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(owner)
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {refresh.access_token}"
    return client
