from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import CompanyMember, Role
from auth_app.permissions import can_manage_leads, get_membership, get_user_leads, get_user_projects, is_company_admin

from .models import CRM, Company, Lead, Project
from .serializers import (
    CompanyAdminSerializer,
    CompanyCreateSerializer,
    CompanySerializer,
    CompanyUpdateSerializer,
    LeadCreateSerializer,
    LeadSerializer,
    ProjectSerializer,
)

class CompanyListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.all()
        return Response(CompanySerializer(companies, many=True).data)


class CompanyCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response({"detail": "You already belong to a company."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CompanyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        company = serializer.save()
        admin_role, _ = Role.objects.get_or_create(
            company=company,
            name=Role.RoleName.ADMIN,
            defaults={"is_default": False},
        )
        CompanyMember.objects.create(user=request.user, company=company, role=admin_role, is_active=True)
        CRM.objects.get_or_create(company=company)

        return Response(CompanySerializer(company).data, status=status.HTTP_201_CREATED)


class MyCompanyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = CompanyAdminSerializer if is_company_admin(request.user, membership.company) else CompanySerializer
        return Response(serializer_class(membership.company).data)

    def patch(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can update company details."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CompanyUpdateSerializer(membership.company, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        company = serializer.save()
        return Response(CompanyAdminSerializer(company).data)


class ProjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)

        projects = get_user_projects(request.user, membership.company)
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not is_company_admin(request.user, membership.company):
            return Response({"detail": "Only admins can create projects."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project = serializer.save(company=membership.company)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class LeadListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company).select_related("project", "source")
        return Response(LeadSerializer(leads, many=True).data)


class LeadCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = get_membership(request.user)
        if not membership:
            return Response({"detail": "No company found."}, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_leads(request.user, membership.company):
            return Response({"detail": "Only admins and editors can create leads."}, status=status.HTTP_403_FORBIDDEN)

        serializer = LeadCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project = serializer.validated_data.get("project")
        if project and project.company_id != membership.company_id:
            return Response({"detail": "Project does not belong to your company."}, status=status.HTTP_400_BAD_REQUEST)

        crm = serializer.validated_data.get("crm")
        if crm and crm.company_id != membership.company_id:
            return Response({"detail": "CRM does not belong to your company."}, status=status.HTTP_400_BAD_REQUEST)

        lead = serializer.save(company=membership.company)
        return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED)
