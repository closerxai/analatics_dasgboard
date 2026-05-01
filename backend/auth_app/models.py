from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    objects = CustomUserManager()

    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email


class Role(models.Model):
    class RoleName(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    name = models.CharField(max_length=20, choices=RoleName.choices)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("name",)]
        ordering = ["name"]

    def __str__(self):
        return self.get_name_display()


class CompanyMember(models.Model):
    user = models.ForeignKey(
        "auth_app.CustomUser", on_delete=models.CASCADE, related_name="company_memberships"
    )
    company = models.ForeignKey(
        "crm.Company", on_delete=models.CASCADE, related_name="members"
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name="members")
    projects = models.ManyToManyField("crm.Project", blank=True, related_name="assigned_members")
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "company")
        ordering = ["company_id", "user_id"]

    def __str__(self):
        return f"{self.user.email} - {self.company.name}"


class JoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    email = models.EmailField()
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    company = models.ForeignKey(
        "crm.Company", on_delete=models.CASCADE, related_name="join_requests"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} -> {self.company.name} ({self.status})"


class Invitation(models.Model):
    email = models.EmailField()
    user = models.ForeignKey(
        "auth_app.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pending_invitations",
    )
    company = models.ForeignKey(
        "crm.Company", on_delete=models.CASCADE, related_name="invitations"
    )
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="invitations"
    )
    token = models.CharField(max_length=255, unique=True)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invite {self.email} to {self.company.name}"
