from django.contrib import admin

from .models import CRM, CRMSecrets, Company, GHLPipelineStage, Lead, LeadSource, Project, SyncLog, Tag


admin.site.register(Company)
admin.site.register(Project)
admin.site.register(CRMSecrets)
admin.site.register(CRM)
admin.site.register(Tag)
admin.site.register(LeadSource)
admin.site.register(Lead)
admin.site.register(GHLPipelineStage)
admin.site.register(SyncLog)
