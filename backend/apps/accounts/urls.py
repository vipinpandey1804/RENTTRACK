"""Auth and accounts API URLs."""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    AcceptInviteView,
    ChangePasswordView,
    InviteView,
    LogoutView,
    MeView,
    MembersView,
    ResendVerificationView,
    SignupView,
    SwitchOrgView,
    ValidateInviteView,
    VerifyEmailView,
)

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change_password"),
    # Email verification
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
    # Invite flow
    path("invite/", InviteView.as_view(), name="invite"),
    path("invite/<str:token>/", ValidateInviteView.as_view(), name="validate_invite"),
    path("accept-invite/", AcceptInviteView.as_view(), name="accept_invite"),
    # Members / org management
    path("members/", MembersView.as_view(), name="members"),
    path("switch-org/", SwitchOrgView.as_view(), name="switch_org"),
]
