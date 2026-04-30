from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    # Auth
    MeAPIView,
    # Company
    CompanyListAPIView, CompanyCreateAPIView, MyCompanyAPIView,
    # Members / Roles
    CompanyMemberListAPIView, CompanyMemberCreateAPIView,
    RoleListAPIView, RoleDetailAPIView, PermissionListAPIView, RBACScanAPIView, AssignProjectsAPIView,
    InvitationListCreateAPIView, InvitationAcceptAPIView,
    JoinRequestCreateAPIView, JoinRequestListAPIView, JoinRequestApproveAPIView, JoinRequestRejectAPIView,
    # Projects
    ProjectListCreateAPIView,
    # Leads
    LeadListAPIView,
    # Analytics
    AnalyticsKPIView, AnalyticsSourceView, AnalyticsAgentView,
    AnalyticsPipelineView, AnalyticsSourceWiseView,
    # GHL Integration
    GHLConnectView, GHLRegisterWebhookView,
    # Sync
    TriggerAutoSyncView, ManualSyncView, SyncLogListView,
    # Webhook (public)
    GHLWebhookView,
)

urlpatterns = [
    # ── Auth ──
    # path('signup/', SignupAPIView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', MeAPIView.as_view(), name='me'),

    # ── Company ──
    path('companies/', CompanyListAPIView.as_view(), name='company-list'),
    path('companies/create/', CompanyCreateAPIView.as_view(), name='company-create'),
    path('my-company/', MyCompanyAPIView.as_view(), name='my-company'),

    # ── Members / Roles ──
    path('company-members/', CompanyMemberListAPIView.as_view(), name='company-member-list'),
    path('company-members/create/', CompanyMemberCreateAPIView.as_view(), name='company-member-create'),
    path('company-members/<int:member_id>/assign-projects/', AssignProjectsAPIView.as_view(), name='assign-projects'),
    path('roles/', RoleListAPIView.as_view(), name='role-list'),
    path('roles/<int:role_id>/', RoleDetailAPIView.as_view(), name='role-detail'),
    path('permissions/', PermissionListAPIView.as_view(), name='permission-list'),
    path('rbac/scan/', RBACScanAPIView.as_view(), name='rbac-scan'),

    # ── Invitations / Join requests ──
    path('invitations/', InvitationListCreateAPIView.as_view(), name='invitation-list-create'),
    path('invitations/accept/', InvitationAcceptAPIView.as_view(), name='invitation-accept'),
    path('join-requests/', JoinRequestCreateAPIView.as_view(), name='join-request-create'),
    path('join-requests/list/', JoinRequestListAPIView.as_view(), name='join-request-list'),
    path('join-requests/<int:join_request_id>/approve/', JoinRequestApproveAPIView.as_view(), name='join-request-approve'),
    path('join-requests/<int:join_request_id>/reject/', JoinRequestRejectAPIView.as_view(), name='join-request-reject'),

    # ── Projects ──
    path('projects/', ProjectListCreateAPIView.as_view(), name='project-list-create'),

    # ── Leads ──
    path('leads/', LeadListAPIView.as_view(), name='lead-list'),

    # ── Analytics ──
    path('analytics/kpis/', AnalyticsKPIView.as_view(), name='analytics-kpis'),
    path('analytics/sources/', AnalyticsSourceView.as_view(), name='analytics-sources'),
    path('analytics/agents/', AnalyticsAgentView.as_view(), name='analytics-agents'),
    path('analytics/pipeline/', AnalyticsPipelineView.as_view(), name='analytics-pipeline'),
    path('analytics/source-wise/', AnalyticsSourceWiseView.as_view(), name='analytics-source-wise'),

    # ── GHL Integration ──
    path('integrations/ghl/', GHLConnectView.as_view(), name='ghl-connect'),
    path('integrations/ghl/webhook/register/', GHLRegisterWebhookView.as_view(), name='ghl-webhook-register'),

    # ── Sync ──
    path('sync/auto/', TriggerAutoSyncView.as_view(), name='sync-auto'),
    path('sync/manual/', ManualSyncView.as_view(), name='sync-manual'),
    path('sync/logs/', SyncLogListView.as_view(), name='sync-logs'),

    # ── Inbound Webhook (public — no auth) ──
    path('webhook/ghl/', GHLWebhookView.as_view(), name='webhook-ghl'),
]
