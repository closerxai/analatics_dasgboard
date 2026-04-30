from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class Company(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    agni_api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Project(models.Model):
    name = models.CharField(max_length=255)
    external_pipeline_id = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class CRMSecrets(models.Model):
    AUTH_TYPE_CHOICES = [
        ('oauth', 'OAuth'),
        ('apikey', 'API Key'),
    ]

    CRM_NAME_CHOICES = [
        ('ghl', 'GoHighLevel'),
        ('salesforce', 'Salesforce'),
        ('zoho', 'Zoho'),
    ]

    name = models.CharField(max_length=50, choices=CRM_NAME_CHOICES)
    auth_type = models.CharField(max_length=10, choices=AUTH_TYPE_CHOICES)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.auth_type == 'apikey' and not self.api_key:
            raise ValidationError("API key is required for API Key authentication")

        if self.auth_type == 'oauth' and not self.access_token:
            raise ValidationError("Access token is required for OAuth")

    def __str__(self):
        return f"{self.get_name_display()} ({self.auth_type})"
    
class CRM(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='crm')
    ghl = models.OneToOneField(CRMSecrets, on_delete=models.SET_NULL, null=True, blank=True, related_name='ghl_crm')
    salesforce = models.OneToOneField(CRMSecrets, on_delete=models.SET_NULL, null=True, blank=True, related_name='salesforce_crm')
    zoho = models.OneToOneField(CRMSecrets, on_delete=models.SET_NULL, null=True, blank=True, related_name='zoho_crm')
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
    tags = models.ManyToManyField(Tag, blank=True, related_name='sources')

    def __str__(self):
        return self.name

class Lead(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leads')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='leads', null=True, blank=True)
    crm = models.ForeignKey(CRM, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    source = models.ForeignKey( LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    tags = models.ManyToManyField(Tag, blank=True, related_name='leads')
    external_id = models.CharField(max_length=255, null=True, blank=True)
    raw_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"
    
class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Role(models.Model):
    name = models.CharField(max_length=50)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class CompanyMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    projects = models.ManyToManyField(Project, blank=True, related_name='assigned_members')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user} - {self.company.name}"
    
class JoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} -> {self.company} ({self.status})"
    
class Invitation(models.Model):
    email = models.EmailField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invitations')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    token = models.CharField(max_length=255, unique=True)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite {self.email} to {self.company.name}"
