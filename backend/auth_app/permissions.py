from django.conf import settings
from rest_framework.permissions import BasePermission

from auth_app.models import CompanyMember, Role
from crm.models import Lead, Project


class HasAccessKey(BasePermission):
    def has_permission(self, request, view):
        return request.headers.get("X-ACCESS-KEY") == settings.ACCESS_KEY


def get_membership(user):
    return (
        CompanyMember.objects.filter(user=user, is_active=True)
        .select_related("company", "role")
        .first()
    )


def is_company_admin(user, company):
    return CompanyMember.objects.filter(
        user=user,
        company=company,
        role__name=Role.RoleName.ADMIN,
        is_active=True,
    ).exists()


def can_manage_leads(user, company):
    return CompanyMember.objects.filter(
        user=user,
        company=company,
        role__name__in=[Role.RoleName.ADMIN, Role.RoleName.EDITOR],
        is_active=True,
    ).exists()


def get_user_projects(user, company):
    membership = get_membership(user)
    if not membership or membership.company_id != company.id:
        return Project.objects.none()

    if is_company_admin(user, company):
        return Project.objects.filter(company=company)

    return membership.projects.all()


def get_user_leads(user, company):
    if is_company_admin(user, company):
        return Lead.objects.filter(company=company)

    projects = get_user_projects(user, company)
    if not projects.exists():
        return Lead.objects.none()

    return Lead.objects.filter(company=company, project__in=projects)
