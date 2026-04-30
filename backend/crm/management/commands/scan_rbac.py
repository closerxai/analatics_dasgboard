from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from auth_app.models import CompanyMember, Role
from crm.models import Company


User = get_user_model()


class Command(BaseCommand):
    help = "Print a quick scan of companies, members, and fixed roles."

    def add_arguments(self, parser):
        parser.add_argument("--company-id", type=int, default=None, help="Only scan a single company id")
        parser.add_argument("--email", type=str, default=None, help="Only show memberships for a user email")

    def handle(self, *args, **options):
        company_id = options.get("company_id")
        email = options.get("email")

        companies = Company.objects.all().order_by("id")
        if company_id is not None:
            companies = companies.filter(id=company_id)

        if not companies.exists():
            self.stdout.write(self.style.WARNING("No companies found for the given filter."))
            return

        for company in companies:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(f"Company #{company.id}: {company.name}"))

            roles = Role.objects.filter(company=company).order_by("name")
            self.stdout.write(self.style.HTTP_INFO("Roles:"))
            if not roles:
                self.stdout.write("  (none)")
            for role in roles:
                self.stdout.write(f"  - {role.get_name_display()} (id={role.id}, default={role.is_default})")

            members = (
                CompanyMember.objects.filter(company=company)
                .select_related("user", "role")
                .prefetch_related("projects")
                .order_by("-is_active", "user__email")
            )
            if email:
                members = members.filter(user__email=email)

            self.stdout.write(self.style.HTTP_INFO("Members:"))
            if not members.exists():
                self.stdout.write("  (none)")
                continue

            for m in members:
                role_name = m.role.get_name_display() if m.role else "(no role)"
                projects = list(m.projects.values_list("name", flat=True).order_by("name"))
                self.stdout.write(
                    f"  - {m.user.email} "
                    f"(member_id={m.id}, active={m.is_active}, role={role_name}) "
                    f"projects={','.join(projects) if projects else '(none)'}"
                )

