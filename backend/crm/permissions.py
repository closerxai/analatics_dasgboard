from .models import CompanyMember, Project, Lead

def has_permission(user, company, perm_code):
    return CompanyMember.objects.filter(
        user=user,
        company=company,
        role__permissions__code=perm_code,
        is_active=True
    ).exists()

def get_user_projects(user, company):
    membership = CompanyMember.objects.filter(
        user=user,
        company=company,
        is_active=True
    ).first()

    if not membership:
        return Project.objects.none()

    return membership.projects.all()

def get_user_leads(user, company):
    projects = get_user_projects(user, company)
    return Lead.objects.filter(company=company, project__in=projects)

def is_company_admin(user, company):
    return CompanyMember.objects.filter(
        user=user,
        company=company,
        role__name='Admin',
        is_active=True
    ).exists()
