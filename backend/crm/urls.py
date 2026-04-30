from django.urls import path
from .views import CompanyListAPIView, LeadListAPIView, SignupAPIView, CompanyMemberCreateAPIView, AssignProjectsAPIView
from .views import CompanyCreateAPIView, MeAPIView, MyCompanyAPIView, CompanyMemberListAPIView, RoleListAPIView, LeadCreateAPIView
from .views import ForgotPasswordAPIView, ResetPasswordAPIView, ForgotEmailAPIView, AdminUserCreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('companies/', CompanyListAPIView.as_view(), name='company-list'),
    path('leads/', LeadListAPIView.as_view(), name='lead-list'),
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('companies/create/', CompanyCreateAPIView.as_view(), name='company-create'),
    path('me/', MeAPIView.as_view(), name='me'),
    path('my-company/', MyCompanyAPIView.as_view(), name='my-company'),
    path('company-members/', CompanyMemberListAPIView.as_view(), name='company-member-list'),
    path('roles/', RoleListAPIView.as_view(), name='role-list'),
    path('company-members/create/', CompanyMemberCreateAPIView.as_view(), name='company-member-create'),
    path('company-members/<int:member_id>/assign-projects/', AssignProjectsAPIView.as_view(), name='assign-projects'),
    path('leads/create/', LeadCreateAPIView.as_view(), name='lead-create'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordAPIView.as_view(), name='reset-password'),
    path('forgot-email/', ForgotEmailAPIView.as_view(), name='forgot-email'),
    path('superuser/create-admin-user/', AdminUserCreateAPIView.as_view(), name='superuser-create-admin-user'),
]
