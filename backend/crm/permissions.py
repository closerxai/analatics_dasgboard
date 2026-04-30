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

    # Admins can access all projects in the company by default.
    if is_company_admin(user, company):
        return Project.objects.filter(company=company)

    return membership.projects.all()

def get_user_leads(user, company):
    # Admins should be able to see all company leads (including unassigned/null project leads).
    if is_company_admin(user, company):
        return Lead.objects.filter(company=company)

    projects = get_user_projects(user, company)
    if not projects.exists():
        return Lead.objects.none()
    return Lead.objects.filter(company=company, project__in=projects)

def is_company_admin(user, company):
    return CompanyMember.objects.filter(
        user=user,
        company=company,
        role__name='Admin',
        is_active=True
    ).exists()
