import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from crm.models import Company

from .email_sender import send_email, welcome_template
from .models import CompanyMember, Invitation, JoinRequest, Role
from .permissions import HasAccessKey, get_membership, is_company_admin
from .serializers import (
    AdminUserCreateSerializer,
    AssignProjectsSerializer,
    CompanyMemberSerializer,
    ForgotEmailSerializer,
    ForgotPasswordSerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    JoinRequestCreateSerializer,
    JoinRequestSerializer,
    ResetPasswordSerializer,
    RoleSerializer,
    SignupSerializer,
    UserSerializer,
)

User = get_user_model()





class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class RoleListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)

        roles = Role.objects.filter(company=membership.company)
        return Response(RoleSerializer(roles, many=True).data)


class CompanyMemberListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can view company members."}, status=status.HTTP_403_FORBIDDEN)

        members = (
            CompanyMember.objects.filter(company=membership.company, is_active=True)
            .select_related("user", "role")
            .prefetch_related("projects")
        )
        return Response(CompanyMemberSerializer(members, many=True).data)


class AssignProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, member_id):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can assign projects."}, status=status.HTTP_403_FORBIDDEN)

        member = (
            CompanyMember.objects.filter(id=member_id, company=membership.company, is_active=True)
            .prefetch_related("projects")
            .first()
        )
        if not member:
            return Response({"detail": "Company member not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignProjectsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        projects = membership.company.projects.filter(id__in=serializer.validated_data["project_ids"])
        member.projects.set(projects)
        return Response({"message": "Projects assigned successfully"})


class InvitationListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can view invitations."}, status=status.HTTP_403_FORBIDDEN)

        invitations = Invitation.objects.filter(company=membership.company).select_related("role")
        return Response(InvitationSerializer(invitations, many=True).data)

    def post(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can invite members."}, status=status.HTTP_403_FORBIDDEN)

        serializer = InvitationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = None
        role_id = serializer.validated_data.get("role_id")
        if role_id is not None:
            role = Role.objects.filter(id=role_id, company=membership.company).first()
            if not role:
                return Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        invite = Invitation.objects.create(
            email=serializer.validated_data["email"],
            company=membership.company,
            role=role,
            token=secrets.token_urlsafe(32),
        )
        return Response(InvitationSerializer(invite).data, status=status.HTTP_201_CREATED)


class InvitationAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invitation = Invitation.objects.filter(token=serializer.validated_data["token"]).select_related("company", "role").first()
        if not invitation or invitation.is_accepted:
            return Response({"detail": "Invalid or expired invitation."}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.email.lower() != invitation.email.lower():
            return Response({"detail": "This invitation does not match your account email."}, status=status.HTTP_403_FORBIDDEN)
        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response({"detail": "You already belong to a company."}, status=status.HTTP_400_BAD_REQUEST)

        role = invitation.role or Role.objects.filter(company=invitation.company, is_default=True).first()
        if not role:
            return Response({"detail": "No default role found for this company."}, status=status.HTTP_400_BAD_REQUEST)

        CompanyMember.objects.create(user=request.user, company=invitation.company, role=role, is_active=True)
        invitation.is_accepted = True
        invitation.save(update_fields=["is_accepted"])
        return Response({"message": "Invitation accepted successfully"})


class JoinRequestCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response({"detail": "You already belong to a company."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JoinRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        join_request = JoinRequest.objects.create(
            user=request.user,
            company_id=serializer.validated_data["company_id"],
            message=serializer.validated_data["message"],
        )
        return Response(JoinRequestSerializer(join_request).data, status=status.HTTP_201_CREATED)


class JoinRequestListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can view join requests."}, status=status.HTTP_403_FORBIDDEN)

        join_requests = JoinRequest.objects.filter(company=membership.company).select_related("user", "company")
        return Response(JoinRequestSerializer(join_requests, many=True).data)


class JoinRequestApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, join_request_id):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can approve join requests."}, status=status.HTTP_403_FORBIDDEN)

        join_request = JoinRequest.objects.filter(
            id=join_request_id,
            company=membership.company,
            status=JoinRequest.Status.PENDING,
        ).select_related("user", "company").first()
        if not join_request:
            return Response({"detail": "Join request not found."}, status=status.HTTP_404_NOT_FOUND)

        role = Role.objects.filter(company=membership.company, is_default=True).first()
        if not role:
            return Response({"detail": "No default role found."}, status=status.HTTP_400_BAD_REQUEST)

        CompanyMember.objects.create(user=join_request.user, company=membership.company, role=role, is_active=True)
        join_request.status = JoinRequest.Status.APPROVED
        join_request.save(update_fields=["status"])
        return Response({"message": "Join request approved."})


class JoinRequestRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, join_request_id):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can reject join requests."}, status=status.HTTP_403_FORBIDDEN)

        join_request = JoinRequest.objects.filter(
            id=join_request_id,
            company=membership.company,
            status=JoinRequest.Status.PENDING,
        ).first()
        if not join_request:
            return Response({"detail": "Join request not found."}, status=status.HTTP_404_NOT_FOUND)

        join_request.status = JoinRequest.Status.REJECTED
        join_request.save(update_fields=["status"])
        return Response({"message": "Join request rejected."})


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.SITE_URL}/reset-password/?uid={uid}&token={token}"
            send_email(
                "Reset your password",
                f"<p>Use this link to reset your password:</p><p>{reset_link}</p>",
                [user.email],
            )

        return Response({"message": "If an account exists, a recovery email has been sent."})


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"message": "Password reset successful."})


class ForgotEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=serializer.validated_data["phone_number"]).first()
        if user:
            send_email(
                "Email recovery",
                f"<p>Your account email is <strong>{user.email}</strong>.</p>",
                [user.email],
            )

        return Response({"message": "If an account exists, a recovery email has been sent."})


class AdminUserCreateAPIView(APIView):
    permission_classes = [HasAccessKey]
    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            return Response({"detail": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
        phone_number = serializer.validated_data.get("phone_number") or None
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            return Response({"detail": "A user with this phone number already exists."}, status=status.HTTP_400_BAD_REQUEST)
        company_name = serializer.validated_data.get("company_name", "").strip()
        with transaction.atomic():
            password = get_random_string(10)
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=serializer.validated_data.get("first_name", ""),
                last_name=serializer.validated_data.get("last_name", ""),
                phone_number=phone_number,
                is_staff=False,
            )

            company = Company.objects.create(
                name=company_name,
                is_active=True,
            )
            role, _ = Role.objects.get_or_create(
                name=Role.RoleName.ADMIN,
                defaults={"is_default": False},
            )
            CompanyMember.objects.create(
                user=user,
                company=company,
                role=role,
                is_active=True,
            )
            welcome_template(
                email=email,
                password=password,
                first_name=serializer.validated_data.get("first_name", ""),
                last_name=serializer.validated_data.get("last_name", ""),
                company_name=company.name if company else None,
                is_admin=bool(company),
            )

        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)

