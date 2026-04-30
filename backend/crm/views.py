from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Company, Lead, CompanyMember, Role, Permission, Project
from .serializers import CompanySerializer, LeadSerializer, SignupSerializer, AssignProjectsSerializer
from .serializers import CompanyCreateSerializer, UserSerializer, CompanyMemberSerializer, RoleSerializer, CompanyMemberCreateSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .permissions import is_company_admin, get_user_leads

User = get_user_model()

class CompanyListAPIView(APIView):
    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

class LeadListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        leads = get_user_leads(request.user, membership.company)
        serializer = LeadSerializer(leads, many=True)
        return Response(serializer.data)
    
class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'User created successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CompanyCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if CompanyMember.objects.filter(user=request.user, is_active=True).exists():
            return Response(
                {'detail': 'You already belong to a company.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = CompanyCreateSerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save()

            admin_role, _ = Role.objects.get_or_create(
                company=company,
                name='Admin',
                defaults={'is_default': True}
            )
            admin_role.permissions.set(Permission.objects.all())
            CompanyMember.objects.get_or_create(
                user=request.user,
                company=company,
                defaults={
                    'role': admin_role,
                    'is_active': True,
                }
            )

            return Response(CompanySerializer(company).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
class MyCompanyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompanySerializer(membership.company)
        return Response(serializer.data)
    
class CompanyMemberListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if not is_company_admin(request.user, membership.company):
            return Response(
                {'detail': 'Only admins can view company members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        members = CompanyMember.objects.filter(
            company=membership.company,
            is_active=True
        ).select_related('user', 'role')

        serializer = CompanyMemberSerializer(members, many=True)
        return Response(serializer.data)
    
class RoleListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        roles = Role.objects.filter(company=membership.company)
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)

class CompanyMemberCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)
        
        if not is_company_admin(request.user, membership.company):
            return Response(
                {'detail': 'Only admins can create company members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CompanyMemberCreateSerializer(data=request.data)
        if serializer.is_valid():
            role = Role.objects.filter(
                id=serializer.validated_data['role'],
                company=membership.company
            ).first()

            if not role:
                return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(username=serializer.validated_data['username']).exists():
                return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            CompanyMember.objects.create(
                user=user,
                company=membership.company,
                role=role,
                is_active=True
            )

            return Response({'message': 'Company member created successfully'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AssignProjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, member_id):
        membership = CompanyMember.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('company').first()

        if not membership:
            return Response({'detail': 'No company found.'}, status=status.HTTP_404_NOT_FOUND)

        if not is_company_admin(request.user, membership.company):
            return Response(
                {'detail': 'Only admins can assign projects.'},
                status=status.HTTP_403_FORBIDDEN
            )

        member = CompanyMember.objects.filter(
            id=member_id,
            company=membership.company,
            is_active=True
        ).first()

        if not member:
            return Response({'detail': 'Company member not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignProjectsSerializer(data=request.data)
        if serializer.is_valid():
            projects = Project.objects.filter(
                id__in=serializer.validated_data['project_ids'],
                company=membership.company
            )

            member.projects.set(projects)

            return Response({'message': 'Projects assigned successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
