from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from crm.models import Company, CompanyMember, Role


User = get_user_model()


class Command(BaseCommand):
    help = "Print a quick scan of companies, members, roles, and permission codes."

    def add_arguments(self, parser):
        parser.add_argument("--company-id", type=int, default=None, help="Only scan a single company id")
        parser.add_argument("--username", type=str, default=None, help="Only show memberships for a username")

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        username = options.get("username")

        companies = Company.objects.all().order_by("id")
        if company_id is not None:
            companies = companies.filter(id=company_id)

        if not companies.exists():
            self.stdout.write(self.style.WARNING("No companies found for the given filter."))
            return

        for company in companies:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(f"Company #{company.id}: {company.name}"))

            roles = (
                Role.objects.filter(company=company)
                .prefetch_related("permissions")
                .order_by("name")
            )
            self.stdout.write(self.style.HTTP_INFO("Roles:"))
            if not roles:
                self.stdout.write("  (none)")
            for role in roles:
                codes = list(role.permissions.values_list("code", flat=True).order_by("code"))
                codes_str = ", ".join(codes) if codes else "(no permissions)"
                self.stdout.write(f"  - {role.name} (id={role.id}, default={role.is_default}): {codes_str}")

            members = (
                CompanyMember.objects.filter(company=company)
                .select_related("user", "role")
                .prefetch_related("role__permissions", "projects")
                .order_by("-is_active", "user__username")
            )
            if username:
                members = members.filter(user__username=username)

            self.stdout.write(self.style.HTTP_INFO("Members:"))
            if not members.exists():
                self.stdout.write("  (none)")
                continue

            for m in members:
                role_name = m.role.name if m.role else "(no role)"
                perm_codes = []
                if m.role_id:
                    perm_codes = list(m.role.permissions.values_list("code", flat=True).order_by("code"))
                projects = list(m.projects.values_list("name", flat=True).order_by("name"))
                self.stdout.write(
                    f"  - {m.user.username} <{m.user.email}> "
                    f"(member_id={m.id}, active={m.is_active}, role={role_name}) "
                    f"perms={','.join(perm_codes) if perm_codes else '(none)'} "
                    f"projects={','.join(projects) if projects else '(none)'}"
                )

