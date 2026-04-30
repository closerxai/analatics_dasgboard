from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Company, Lead, CompanyMember, Role, Permission, Project, UserProfile 
from .serializers import CompanySerializer, LeadSerializer, SignupSerializer, AssignProjectsSerializer, LeadCreateSerializer
from .serializers import CompanyCreateSerializer, UserSerializer, CompanyMemberSerializer, RoleSerializer, CompanyMemberCreateSerializer
from .serializers import ForgotPasswordSerializer, ResetPasswordSerializer, ForgotEmailSerializer, AdminUserCreateSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .permissions import is_company_admin, get_user_leads
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

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
