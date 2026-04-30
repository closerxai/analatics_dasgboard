from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import logging
import secrets

from .models import (
    Company, Lead, CompanyMember, Role, Permission, Project,
    CRM, CRMSecrets, GHLPipelineStage, SyncLog, LEAD_STATUS_CHOICES,
    Invitation, JoinRequest,
)
from .serializers import (
    CompanySerializer, CompanyAdminSerializer, LeadSerializer, SignupSerializer, AssignProjectsSerializer,
    CompanyCreateSerializer, CompanyUpdateSerializer, UserSerializer, CompanyMemberSerializer, RoleSerializer,
    CompanyMemberCreateSerializer, ProjectSerializer, SyncLogSerializer,
    GHLConnectSerializer, ManualSyncSerializer,
    RoleWithPermissionsSerializer, CompanyMemberRBACSerializer,
    PermissionSerializer, RoleUpsertSerializer,
    InvitationSerializer, InvitationCreateSerializer, InvitationAcceptSerializer,
    JoinRequestSerializer, JoinRequestCreateSerializer, JoinRequestDecisionSerializer,
)
from .permissions import is_company_admin, get_user_leads
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

User = get_user_model()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────
# Auth views
# ──────────────────────────────────────────────────

# class SignupAPIView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = SignupSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ──────────────────────────────────────────────────
# Company views
# ──────────────────────────────────────────────────

class CompanyListAPIView(APIView):
    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)


class CompanyCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response({'detail': 'You already belong to a company.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompanyCreateSerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save()
            admin_role, _ = Role.objects.get_or_create(
                company=company, name='Admin', defaults={'is_default': True}
            )
            admin_role.permissions.set(Permission.objects.all())
            CompanyMember.objects.get_or_create(
                user=request.user, company=company,
                defaults={'role': admin_role, 'is_active': True}
            )
            # Auto-create CRM record
            CRM.objects.get_or_create(company=company)
            return Response(CompanySerializer(company).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyCompanyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanyAdminSerializer(membership.company) if is_company_admin(request.user, membership.company) else CompanySerializer(membership.company)
        return Response(serializer.data)

    def patch(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can update company details.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CompanyUpdateSerializer(membership.company, data=request.data, partial=True)
        if serializer.is_valid():
            company = serializer.save()
            return Response(CompanySerializer(company).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────────
# Members / Roles views
# ──────────────────────────────────────────────────

class CompanyMemberListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can view company members.'}, status=status.HTTP_403_FORBIDDEN)
        members = CompanyMember.objects.filter(
            company=membership.company, is_active=True
        ).select_related('user', 'role')
        return Response(CompanyMemberSerializer(members, many=True).data)


class CompanyMemberCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can create company members.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CompanyMemberCreateSerializer(data=request.data)
        if serializer.is_valid():
            role = Role.objects.filter(
                id=serializer.validated_data['role'], company=membership.company
            ).first()
            if not role:
                return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=serializer.validated_data['username']).exists():
                return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
            CompanyMember.objects.create(user=user, company=membership.company, role=role, is_active=True)
            return Response({'message': 'Company member created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        roles = Role.objects.filter(company=membership.company)
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can create roles.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RoleUpsertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = Role.objects.create(
            company=membership.company,
            name=serializer.validated_data['name'],
            is_default=serializer.validated_data.get('is_default', False),
        )
        if role.is_default:
            Role.objects.filter(company=membership.company).exclude(id=role.id).update(is_default=False)

        perm_ids = serializer.validated_data.get('permission_ids', [])
        if perm_ids:
            role.permissions.set(Permission.objects.filter(id__in=perm_ids))

        return Response(RoleWithPermissionsSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, role_id: int):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can update roles.'}, status=status.HTTP_403_FORBIDDEN)

        role = Role.objects.filter(id=role_id, company=membership.company).prefetch_related('permissions').first()
        if not role:
            return Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleUpsertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role.name = serializer.validated_data['name']
        role.is_default = serializer.validated_data.get('is_default', role.is_default)
        role.save()
        if role.is_default:
            Role.objects.filter(company=membership.company).exclude(id=role.id).update(is_default=False)

        perm_ids = serializer.validated_data.get('permission_ids', [])
        role.permissions.set(Permission.objects.filter(id__in=perm_ids))

        return Response(RoleWithPermissionsSerializer(role).data)


class PermissionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can view permissions.'}, status=status.HTTP_403_FORBIDDEN)

        perms = Permission.objects.all().order_by('code')
        return Response(PermissionSerializer(perms, many=True).data)


class InvitationListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can view invitations.'}, status=status.HTTP_403_FORBIDDEN)

        invites = Invitation.objects.filter(company=membership.company).select_related('role').order_by('-created_at')[:100]
        return Response(InvitationSerializer(invites, many=True).data)

    def post(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can invite members.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = InvitationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = None
        role_id = serializer.validated_data.get('role_id')
        if role_id is not None:
            role = Role.objects.filter(id=role_id, company=membership.company).first()
            if not role:
                return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)

        token = secrets.token_urlsafe(32)
        # Ensure token uniqueness
        for _ in range(5):
            if not Invitation.objects.filter(token=token).exists():
                break
            token = secrets.token_urlsafe(32)
        else:
            return Response({'detail': 'Failed to generate invitation token.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invite = Invitation.objects.create(
            email=serializer.validated_data['email'],
            company=membership.company,
            role=role,
            token=token,
        )
        return Response(InvitationSerializer(invite).data, status=status.HTTP_201_CREATED)


class InvitationAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invite = Invitation.objects.filter(token=serializer.validated_data['token']).select_related('company', 'role').first()
        if not invite or invite.is_accepted:
            return Response({'detail': 'Invalid or expired invitation.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.email or request.user.email.strip().lower() != invite.email.strip().lower():
            return Response({'detail': 'This invitation does not match your account email.'}, status=status.HTTP_403_FORBIDDEN)

        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response({'detail': 'You already belong to a company.'}, status=status.HTTP_400_BAD_REQUEST)

        role = invite.role or Role.objects.filter(company=invite.company, is_default=True).first()
        if not role:
            return Response({'detail': 'No role assigned to invitation and no default role found.'}, status=status.HTTP_400_BAD_REQUEST)

        CompanyMember.objects.update_or_create(
            user=request.user,
            company=invite.company,
            defaults={'role': role, 'is_active': True},
        )
        invite.is_accepted = True
        invite.save(update_fields=['is_accepted'])

        return Response({'message': 'Invitation accepted successfully', 'company_id': invite.company_id})


class JoinRequestCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response({'detail': 'You already belong to a company.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JoinRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        company = Company.objects.filter(id=serializer.validated_data['company_id']).first()
        if not company:
            return Response({'detail': 'Company not found.'}, status=status.HTTP_404_NOT_FOUND)

        jr = JoinRequest.objects.create(
            user=request.user,
            company=company,
            message=serializer.validated_data.get('message', ''),
        )
        return Response(JoinRequestSerializer(jr).data, status=status.HTTP_201_CREATED)


class JoinRequestListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can view join requests.'}, status=status.HTTP_403_FORBIDDEN)

        reqs = JoinRequest.objects.filter(company=membership.company).select_related('user', 'company').order_by('-created_at')[:100]
        return Response(JoinRequestSerializer(reqs, many=True).data)


class JoinRequestApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, join_request_id: int):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can approve join requests.'}, status=status.HTTP_403_FORBIDDEN)

        jr = JoinRequest.objects.filter(id=join_request_id, company=membership.company).select_related('user', 'company').first()
        if not jr:
            return Response({'detail': 'Join request not found.'}, status=status.HTTP_404_NOT_FOUND)
        if jr.status != 'pending':
            return Response({'detail': 'Join request already processed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JoinRequestDecisionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = None
        role_id = serializer.validated_data.get('role_id')
        if role_id is not None:
            role = Role.objects.filter(id=role_id, company=membership.company).first()
        if not role:
            role = Role.objects.filter(company=membership.company, is_default=True).first()
        if not role:
            return Response({'detail': 'No valid role provided and no default role found.'}, status=status.HTTP_400_BAD_REQUEST)

        CompanyMember.objects.update_or_create(
            user=jr.user,
            company=jr.company,
            defaults={'role': role, 'is_active': True},
        )
        jr.status = 'approved'
        jr.save(update_fields=['status'])

        return Response({'message': 'Join request approved.'})


class JoinRequestRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, join_request_id: int):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can reject join requests.'}, status=status.HTTP_403_FORBIDDEN)

        jr = JoinRequest.objects.filter(id=join_request_id, company=membership.company).first()
        if not jr:
            return Response({'detail': 'Join request not found.'}, status=status.HTTP_404_NOT_FOUND)
        if jr.status != 'pending':
            return Response({'detail': 'Join request already processed.'}, status=status.HTTP_400_BAD_REQUEST)

        jr.status = 'rejected'
        jr.save(update_fields=['status'])
        return Response({'message': 'Join request rejected.'})


class RBACScanAPIView(APIView):
    """
    Scan roles/permissions for the current company.

    - Admins: get full company scan (roles + members + permissions).
    - Non-admins: get only their own membership/role permissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company', 'role').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        admin = is_company_admin(request.user, membership.company)

        if admin:
            roles_qs = Role.objects.filter(company=membership.company).prefetch_related('permissions').order_by('name')
        else:
            roles_qs = Role.objects.filter(id=membership.role_id).prefetch_related('permissions')
        roles_data = RoleWithPermissionsSerializer(roles_qs, many=True).data

        if admin:
            members_qs = (
                CompanyMember.objects.filter(company=membership.company)
                .select_related('user', 'role')
                .prefetch_related('projects', 'role__permissions')
                .order_by('-is_active', 'user__username')
            )
            members_data = CompanyMemberRBACSerializer(members_qs, many=True).data
        else:
            membership_qs = (
                CompanyMember.objects.filter(id=membership.id)
                .select_related('user', 'role')
                .prefetch_related('projects', 'role__permissions')
            )
            members_data = CompanyMemberRBACSerializer(membership_qs, many=True).data

        return Response({
            'company': {'id': membership.company_id, 'name': membership.company.name},
            'viewer': {
                'id': request.user.id,
                'username': request.user.username,
                'is_admin': admin,
                'membership_id': membership.id,
            },
            'roles': roles_data,
            'members': members_data,
        })


class AssignProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, member_id):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can assign projects.'}, status=status.HTTP_403_FORBIDDEN)
        member = CompanyMember.objects.filter(
            id=member_id, company=membership.company, is_active=True
        ).first()
        if not member:
            return Response({'detail': 'Company member not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssignProjectsSerializer(data=request.data)
        if serializer.is_valid():
            projects = Project.objects.filter(
                id__in=serializer.validated_data['project_ids'], company=membership.company
            )
            member.projects.set(projects)
            return Response({'message': 'Projects assigned successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────────
# Project views
# ──────────────────────────────────────────────────

class ProjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        projects = Project.objects.filter(company=membership.company)
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can create projects.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            project = serializer.save(company=membership.company)
            return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────────
# Lead views
# ──────────────────────────────────────────────────

class LeadListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user, is_active=True
        ).select_related('company').first()
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        leads = get_user_leads(request.user, membership.company)

        # Filters
        project_id = request.query_params.get('project')
        source = request.query_params.get('source')
        agent = request.query_params.get('agent')
        city = request.query_params.get('city')
        lead_status = request.query_params.get('status')
        q = request.query_params.get('q', '').strip()

        if project_id and project_id != 'all':
            leads = leads.filter(project_id=project_id)
        if source and source != 'All':
            leads = leads.filter(source__name=source)
        if agent and agent != 'All':
            leads = leads.filter(assigned_to_name__icontains=agent)
        if city and city != 'All':
            leads = leads.filter(city__icontains=city)
        if lead_status and lead_status != 'Any':
            leads = leads.filter(status=lead_status)
        if q:
            leads = leads.filter(
                Q(name__icontains=q) | Q(email__icontains=q) |
                Q(phone__icontains=q) | Q(remarks__icontains=q)
            )

        serializer = LeadSerializer(leads.select_related('source', 'project')[:500], many=True)
        return Response(serializer.data)


# ──────────────────────────────────────────────────
# Analytics views
# ──────────────────────────────────────────────────

def _get_membership(request):
    return CompanyMember.objects.filter(
        user=request.user, is_active=True
    ).select_related('company').first()


class AnalyticsKPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company)

        # Date range (default: last 30 days)
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        recent = leads.filter(created_at__gte=since)
        prev = leads.filter(
            created_at__gte=since - timedelta(days=days),
            created_at__lt=since,
        )

        total = recent.count()
        prev_total = prev.count()
        qualified = recent.filter(status__in=['qualified', 'booked_site_visit', 'site_visit_done']).count()
        site_visits = recent.filter(status__in=['booked_site_visit', 'site_visit_done']).count()
        won = recent.filter(ghl_opportunity_status='won').count()
        conversion = (won / total * 100) if total else 0

        def pct_delta(curr, prev_v):
            if not prev_v:
                return '+0.0%'
            delta = ((curr - prev_v) / prev_v) * 100
            sign = '+' if delta >= 0 else ''
            return f"{sign}{delta:.1f}%"

        kpis = [
            {
                'label': 'Total Leads', 'val': total, 'icon': 'users',
                'delta': pct_delta(total, prev_total), 'up': total >= prev_total, 'accent': 'primary',
            },
            {
                'label': 'Qualified', 'val': qualified, 'icon': 'check',
                'delta': pct_delta(qualified, prev.filter(status__in=['qualified', 'booked_site_visit', 'site_visit_done']).count()),
                'up': True, 'accent': 'primary',
            },
            {
                'label': 'Site Visits Booked', 'val': site_visits, 'icon': 'pin',
                'delta': pct_delta(site_visits, prev.filter(status__in=['booked_site_visit', 'site_visit_done']).count()),
                'up': True, 'accent': 'good',
            },
            {
                'label': 'Deals Closed', 'val': won, 'icon': 'trophy',
                'delta': pct_delta(won, prev.filter(ghl_opportunity_status='won').count()),
                'up': True, 'accent': 'good',
            },
            {
                'label': 'Conversion', 'val': f"{conversion:.1f}%", 'icon': 'funnel',
                'delta': '—', 'up': True, 'accent': 'primary',
            },
        ]
        return Response({'kpis': kpis, 'total': total, 'period_days': days})


class AnalyticsSourceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company)
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        leads = leads.filter(created_at__gte=since)

        project_id = request.query_params.get('project')
        if project_id and project_id != 'all':
            leads = leads.filter(project_id=project_id)

        source_counts = (
            leads.values('source__name')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        sources = [
            {'name': r['source__name'] or 'Unknown', 'total': r['total']}
            for r in source_counts
        ]
        return Response({'sources': sources})


class AnalyticsAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company)
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        leads = leads.filter(created_at__gte=since)

        project_id = request.query_params.get('project')
        if project_id and project_id != 'all':
            leads = leads.filter(project_id=project_id)

        all_statuses = [s[0] for s in LEAD_STATUS_CHOICES]

        agent_counts = (
            leads.values('assigned_to_name')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        rows = []
        for rec in agent_counts:
            agent = rec['assigned_to_name'] or 'Unassigned'
            agent_leads = leads.filter(assigned_to_name=rec['assigned_to_name'])
            by_status = {s: 0 for s in all_statuses}
            for sc in agent_leads.values('status').annotate(n=Count('id')):
                by_status[sc['status']] = sc['n']
            rows.append({
                'agent': agent,
                'total': rec['total'],
                'by_status': by_status,
            })

        return Response({'agents': rows, 'statuses': all_statuses})


class AnalyticsPipelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company)
        project_id = request.query_params.get('project')
        if project_id and project_id != 'all':
            leads = leads.filter(project_id=project_id)

        # GHL pipeline stages
        stages = GHLPipelineStage.objects.filter(
            company=membership.company, is_active=True
        ).order_by('pipeline_id', 'position')

        stage_data = []
        for stage in stages:
            count = leads.filter(ghl_pipeline_stage_id=stage.stage_id).count()
            stage_data.append({
                'stage_id': stage.stage_id,
                'stage_name': stage.stage_name,
                'pipeline_id': stage.pipeline_id,
                'pipeline_name': stage.pipeline_name,
                'position': stage.position,
                'count': count,
                'project_id': stage.project_id,
            })

        # Fallback: group by our local status field if no GHL stages
        if not stage_data:
            for val, label in LEAD_STATUS_CHOICES:
                count = leads.filter(status=val).count()
                stage_data.append({
                    'stage_id': val,
                    'stage_name': label,
                    'pipeline_id': 'local',
                    'pipeline_name': 'Local Pipeline',
                    'position': 0,
                    'count': count,
                    'project_id': None,
                })

        # Include lead cards for each stage (up to 10)
        for s in stage_data:
            if s['pipeline_id'] == 'local':
                stage_leads = leads.filter(status=s['stage_id'])
            else:
                stage_leads = leads.filter(ghl_pipeline_stage_id=s['stage_id'])
            s['leads'] = LeadSerializer(
                stage_leads.select_related('source', 'project')[:10], many=True
            ).data

        return Response({'stages': stage_data})


class AnalyticsSourceWiseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company)
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        leads = leads.filter(created_at__gte=since)

        project_id = request.query_params.get('project')
        if project_id and project_id != 'all':
            leads = leads.filter(project_id=project_id)

        # Build source × status matrix
        all_statuses = [s[0] for s in LEAD_STATUS_CHOICES]
        source_names = list(
            leads.values_list('source__name', flat=True).distinct()
        )

        rows = []
        for sname in source_names:
            sl = leads.filter(source__name=sname)
            by_status = {s: 0 for s in all_statuses}
            for sc in sl.values('status').annotate(n=Count('id')):
                by_status[sc['status']] = sc['n']
            rows.append({
                'source': sname or 'Unknown',
                'total': sl.count(),
                'by_status': by_status,
            })

        rows.sort(key=lambda x: x['total'], reverse=True)
        return Response({'rows': rows, 'statuses': all_statuses, 'total': leads.count()})


# ──────────────────────────────────────────────────
# GHL Integration views
# ──────────────────────────────────────────────────

class GHLConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can connect integrations.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = GHLConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        company = membership.company
        data = serializer.validated_data

        # Create or update CRMSecrets for GHL
        crm, _ = CRM.objects.get_or_create(company=company)
        if crm.ghl:
            secret = crm.ghl
            secret.api_key = data.get('api_key')
            secret.access_token = data.get('access_token')
            secret.location_id = data.get('location_id')
            secret.auth_type = 'apikey' if data.get('api_key') else 'oauth'
            secret.save()
        else:
            secret = CRMSecrets.objects.create(
                name='ghl',
                auth_type='apikey' if data.get('api_key') else 'oauth',
                api_key=data.get('api_key'),
                access_token=data.get('access_token'),
                location_id=data.get('location_id'),
            )
            crm.ghl = secret
            crm.save()

        return Response({'message': 'GHL connected successfully', 'location_id': data.get('location_id')})

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        company = membership.company
        try:
            crm = company.crm
            if crm and crm.ghl:
                return Response({
                    'connected': True,
                    'location_id': crm.ghl.location_id,
                    'auth_type': crm.ghl.auth_type,
                    'webhook_registered': bool(crm.ghl.webhook_id),
                })
        except Exception:
            pass
        return Response({'connected': False})


class GHLRegisterWebhookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can register webhooks.'}, status=status.HTTP_403_FORBIDDEN)

        webhook_base_url = request.data.get('webhook_base_url', '').strip()
        if not webhook_base_url:
            # Try to derive from request
            webhook_base_url = f"{request.scheme}://{request.get_host()}"

        try:
            from .utils.ghl_webhook import register_webhook_for_company
            webhook_id = register_webhook_for_company(membership.company, webhook_base_url)
            return Response({'message': 'Webhook registered', 'webhook_id': webhook_id})
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────────
# Sync views
# ──────────────────────────────────────────────────

class TriggerAutoSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can trigger syncs.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            from .utils.ghl_sync import auto_sync_company
            sync_log = auto_sync_company(membership.company)
            if sync_log:
                return Response(SyncLogSerializer(sync_log).data)
            return Response({'detail': 'No GHL credentials configured.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManualSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({'detail': 'Only admins can trigger syncs.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ManualSyncSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        date_from = serializer.validated_data['date_from']
        date_to = serializer.validated_data['date_to']

        try:
            from .utils.ghl_sync import manual_sync_company
            sync_log = manual_sync_company(
                membership.company, date_from, date_to,
                triggered_by=request.user,
            )
            return Response(SyncLogSerializer(sync_log).data)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = _get_membership(request)
        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        logs = SyncLog.objects.filter(company=membership.company)[:50]
        return Response(SyncLogSerializer(logs, many=True).data)


# ──────────────────────────────────────────────────
# Webhook inbound endpoint
# ──────────────────────────────────────────────────

class GHLWebhookView(APIView):
    """
    Public endpoint — no auth required.
    GHL posts events here. We verify signature then process.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.data
        location_id = (
            payload.get("locationId")
            or payload.get("location_id")
            or request.headers.get("X-Ghl-Location-Id", "")
        )

        try:
            from .utils.ghl_webhook import handle_webhook_event
            result = handle_webhook_event(payload, location_id)
            return Response(result)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return Response({'detail': 'Internal error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeadCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = LeadCreateSerializer(data=request.data)
        if serializer.is_valid():
            project = serializer.validated_data['project']

            if project.company_id != membership.company_id:
                return Response(
                    {'detail': 'Project does not belong to your company.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            lead = serializer.save(company=membership.company)
            return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordAPIView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.filter(email=serializer.validated_data['email']).first()

            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = f"{settings.SITE_URL}/reset-password/?uid={uid}&token={token}"
                send_mail(
                    subject='Reset your password',
                    message=f'Use this link to reset your password: {reset_link}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                return Response(
                    {
                        'message': 'Password reset link generated successfully.',
                        'reset_link': reset_link
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {'detail': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordAPIView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({'detail': 'Invalid user.'}, status=status.HTTP_400_BAD_REQUEST)

            if not default_token_generator.check_token(user, serializer.validated_data['token']):
                return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ForgotEmailAPIView(APIView):
    def post(self, request):
        serializer = ForgotEmailSerializer(data=request.data)
        if serializer.is_valid():
            profile = UserProfile.objects.filter(
                phone_number=serializer.validated_data['phone_number']
            ).select_related('user').first()

            if profile:
                return Response(
                    {'message': 'If an account exists, a recovery email has been sent.'},
                    status=status.HTTP_200_OK
                )

            return Response(
                {'message': 'If an account exists, a recovery email has been sent.'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AdminUserCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only superusers can create admin users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AdminUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            phone_number = serializer.validated_data.get('phone_number')
            company_id = serializer.validated_data.get('company')

            if User.objects.filter(email=email).exists():
                return Response(
                    {'detail': 'A user with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            password = get_random_string(10)
            username = email.split('@')[0]

            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True
            )

            if phone_number:
                UserProfile.objects.create(
                    user=user,
                    phone_number=phone_number
                )

            if company_id:
                company = Company.objects.filter(id=company_id).first()
                if not company:
                    return Response(
                        {'detail': 'Invalid company.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                admin_role, _ = Role.objects.get_or_create(
                    company=company,
                    name='Admin',
                    defaults={'is_default': True}
                )
                admin_role.permissions.set(Permission.objects.all())

                CompanyMember.objects.get_or_create(
                    user=user,
                    company=company,
                    defaults={
                        'role': admin_role,
                        'is_active': True,
                    }
                )

            send_mail(
                subject='Your admin account has been created',
                message=f'Your username is {username} and your password is {password}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response(
                {'message': 'Admin user created successfully.'},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
