from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    agni_api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=255)
    external_pipeline_id = models.CharField(max_length=255, blank=True, default="")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CRMSecrets(models.Model):
    AUTH_TYPE_CHOICES = [
        ("oauth", "OAuth"),
        ("apikey", "API Key"),
    ]
    CRM_NAME_CHOICES = [
        ("ghl", "GoHighLevel"),
        ("salesforce", "Salesforce"),
        ("zoho", "Zoho"),
    ]

    name = models.CharField(max_length=50, choices=CRM_NAME_CHOICES)
    auth_type = models.CharField(max_length=10, choices=AUTH_TYPE_CHOICES)
    api_key = models.CharField(max_length=500, null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    location_id = models.CharField(max_length=255, null=True, blank=True)
    webhook_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.auth_type == "apikey" and not self.api_key:
            raise ValidationError("API key is required for API Key authentication")
        if self.auth_type == "oauth" and not self.access_token:
            raise ValidationError("Access token is required for OAuth")

    def __str__(self):
        return f"{self.get_name_display()} ({self.auth_type})"


class CRM(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="crm")
    ghl = models.OneToOneField(CRMSecrets, on_delete=models.SET_NULL, null=True, blank=True, related_name="ghl_crm")
    salesforce = models.OneToOneField(
        CRMSecrets,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salesforce_crm",
    )
    zoho = models.OneToOneField(CRMSecrets, on_delete=models.SET_NULL, null=True, blank=True, related_name="zoho_crm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CRM for {self.company.name}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class LeadSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="sources")

    def __str__(self):
        return self.name




class Lead(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="leads")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="leads", null=True, blank=True)
    crm = models.ForeignKey(CRM, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    tags = models.ManyToManyField(Tag, blank=True, related_name="leads")
    status = models.CharField(max_length=500, null=True, blank=True)

    assigned_to_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    planning_for_visit = models.CharField(max_length=255, null=True, blank=True)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    whatsapp_status = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    monetary_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    external_id = models.CharField(max_length=255, null=True, blank=True)
    ghl_opportunity_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    ghl_contact_id = models.CharField(max_length=255, null=True, blank=True)
    ghl_pipeline_id = models.CharField(max_length=255, null=True, blank=True)
    ghl_pipeline_stage_id = models.CharField(max_length=255, null=True, blank=True)
    ghl_pipeline_stage_name = models.CharField(max_length=255, null=True, blank=True)
    ghl_opportunity_status = models.CharField(max_length=50, null=True, blank=True)
    raw_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class GHLPipelineStage(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ghl_stages")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="ghl_stages")
    pipeline_id = models.CharField(max_length=255)
    pipeline_name = models.CharField(max_length=255)
    stage_id = models.CharField(max_length=255)
    stage_name = models.CharField(max_length=255)
    position = models.IntegerField(default=0)
    color = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("company", "stage_id")
        ordering = ["pipeline_id", "position"]

    def __str__(self):
        return f"{self.pipeline_name} -> {self.stage_name}"


class SyncLog(models.Model):
    SYNC_TYPE_CHOICES = [
        ("auto", "Auto Sync"),
        ("manual", "Manual Sync"),
        ("webhook", "Webhook"),
    ]
    STATUS_CHOICES = [
        ("running", "Running"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sync_logs")
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    leads_synced = models.IntegerField(default=0)
    leads_created = models.IntegerField(default=0)
    leads_updated = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    date_from = models.DateTimeField(null=True, blank=True)
    date_to = models.DateTimeField(null=True, blank=True)
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.sync_type} sync for {self.company.name} [{self.status}]"
