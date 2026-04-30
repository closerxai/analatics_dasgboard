from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AdminUserCreateAPIView,
    AssignProjectsAPIView,
    CompanyMemberListAPIView,
    ForgotEmailAPIView,
    ForgotPasswordAPIView,
    InvitationAcceptAPIView,
    InvitationListCreateAPIView,
    JoinRequestApproveAPIView,
    JoinRequestCreateAPIView,
    JoinRequestListAPIView,
    JoinRequestRejectAPIView,
    MeAPIView,
    ResetPasswordAPIView,
    RoleListAPIView,
    SignupAPIView,
)

urlpatterns = [
    path("signup/", SignupAPIView.as_view(), name="signup"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("forgot-email/", ForgotEmailAPIView.as_view(), name="forgot-email"),
    path("roles/", RoleListAPIView.as_view(), name="role-list"),
    path("company-members/", CompanyMemberListAPIView.as_view(), name="company-member-list"),
    path(
        "company-members/<int:member_id>/assign-projects/",
        AssignProjectsAPIView.as_view(),
        name="assign-projects",
    ),
    path("invitations/", InvitationListCreateAPIView.as_view(), name="invitation-list-create"),
    path("invitations/accept/", InvitationAcceptAPIView.as_view(), name="invitation-accept"),
    path("join-requests/", JoinRequestCreateAPIView.as_view(), name="join-request-create"),
    path("join-requests/list/", JoinRequestListAPIView.as_view(), name="join-request-list"),
    path(
        "join-requests/<int:join_request_id>/approve/",
        JoinRequestApproveAPIView.as_view(),
        name="join-request-approve",
    ),
    path(
        "join-requests/<int:join_request_id>/reject/",
        JoinRequestRejectAPIView.as_view(),
        name="join-request-reject",
    ),
    path(
        "superuser/create-admin-user/",
        AdminUserCreateAPIView.as_view(),
        name="superuser-create-admin-user",
    ),
]
