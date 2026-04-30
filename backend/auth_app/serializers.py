from django.contrib.auth import get_user_model
from rest_framework import serializers

from crm.models import Company, Project

from .models import CompanyMember, Invitation, JoinRequest, Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
        ]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone_number", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class RoleSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "label", "is_default"]


class ProjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "external_pipeline_id"]


class CompanyMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    projects = ProjectSummarySerializer(many=True, read_only=True)

    class Meta:
        model = CompanyMember
        fields = ["id", "user", "role", "projects", "is_active", "joined_at"]


class AssignProjectsSerializer(serializers.Serializer):
    project_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class InvitationSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ["id", "email", "role", "token", "is_accepted", "created_at"]


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role_id = serializers.IntegerField(required=False, allow_null=True)


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()


class JoinRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = JoinRequest
        fields = ["id", "user", "company", "company_name", "status", "message", "created_at"]


class JoinRequestCreateSerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_company_id(self, value):
        if not Company.objects.filter(id=value).exists():
            raise serializers.ValidationError("Company not found.")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)


class ForgotEmailSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class AdminUserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    company = serializers.IntegerField(required=False)
    role = serializers.ChoiceField(choices=Role.RoleName.choices, required=False, default=Role.RoleName.ADMIN)
