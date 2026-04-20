"""Auth and accounts API URLs."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    ChangePasswordView,
    InviteView,
    LogoutView,
    MeView,
    MembersView,
    SignupView,
    SwitchOrgView,
)

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("invite/", InviteView.as_view(), name="invite"),
    path("members/", MembersView.as_view(), name="members"),
    path("switch-org/", SwitchOrgView.as_view(), name="switch_org"),
]
