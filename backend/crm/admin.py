from django.contrib import admin
from .models import (
    Company,
    Project,
    CRMSecrets,
    CRM,
    Tag,
    LeadSource,
    Lead,
    Permission,
    Role,
    CompanyMember,
    JoinRequest,
    Invitation,
    UserProfile,
)


admin.site.register(Company)
admin.site.register(Project)
admin.site.register(CRMSecrets)
admin.site.register(CRM)
admin.site.register(Tag)
admin.site.register(LeadSource)
admin.site.register(Lead)
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(CompanyMember)
admin.site.register(JoinRequest)
admin.site.register(Invitation)
admin.site.register(UserProfile)
