from rest_framework import serializers
from .models import Company, Lead, CompanyMember, Role, Project, SyncLog, Permission, Invitation, JoinRequest
from django.contrib.auth import get_user_model

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']


class CompanyAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo', 'agni_api_key', 'is_active', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'external_pipeline_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeadSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True, default='')
    project_name = serializers.CharField(source='project.name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'email', 'phone',
            'status', 'status_display',
            'source', 'source_name',
            'project', 'project_name',
            'assigned_to_name',
            'city',
            'planning_for_visit',
            'follow_up_date',
            'whatsapp_status',
            'remarks',
            'monetary_value',
            'ghl_opportunity_id',
            'ghl_pipeline_stage_name',
            'ghl_opportunity_status',
            'external_id',
            'created_at',
            'updated_at',
        ]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name', 'logo', 'agni_api_key', 'is_active']


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name', 'agni_api_key', 'is_active']


class CompanyMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = CompanyMember
        fields = ['id', 'username', 'email', 'role', 'role_name', 'projects', 'is_active', 'joined_at']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_default']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'description']


class RoleWithPermissionsSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'is_default', 'permissions']


class CompanyMemberRBACSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = RoleWithPermissionsSerializer(read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = CompanyMember
        fields = ['id', 'username', 'email', 'role', 'projects', 'is_active', 'joined_at']


class RoleUpsertSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    is_default = serializers.BooleanField(required=False, default=False)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        default=list,
    )


class InvitationSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True, default=None)

    class Meta:
        model = Invitation
        fields = ['id', 'email', 'company', 'role', 'role_name', 'token', 'is_accepted', 'created_at']
        read_only_fields = ['id', 'token', 'is_accepted', 'created_at']


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role_id = serializers.IntegerField(required=False, allow_null=True)


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()


class JoinRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = JoinRequest
        fields = ['id', 'status', 'message', 'created_at', 'company', 'company_name', 'user', 'username', 'email']
        read_only_fields = ['id', 'created_at', 'status', 'user']


class JoinRequestCreateSerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True, default='')


class JoinRequestDecisionSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=False, allow_null=True)


class CompanyMemberCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.IntegerField()


class AssignProjectsSerializer(serializers.Serializer):
    project_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True
    )


class SyncLogSerializer(serializers.ModelSerializer):
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True, default=None)

    class Meta:
        model = SyncLog
        fields = [
            'id', 'sync_type', 'sync_type_display', 'status', 'status_display',
            'started_at', 'completed_at',
            'leads_synced', 'leads_created', 'leads_updated',
            'error_message', 'date_from', 'date_to',
            'triggered_by_username',
        ]


class GHLConnectSerializer(serializers.Serializer):
    api_key = serializers.CharField(required=False, allow_blank=True)
    access_token = serializers.CharField(required=False, allow_blank=True)
    location_id = serializers.CharField(required=True)

    def validate(self, data):
        if not data.get('api_key') and not data.get('access_token'):
            raise serializers.ValidationError("Either api_key or access_token is required.")
        return data


class ManualSyncSerializer(serializers.Serializer):
    date_from = serializers.DateTimeField()
    date_to = serializers.DateTimeField()

    def validate(self, data):
        if data['date_from'] >= data['date_to']:
            raise serializers.ValidationError("date_from must be before date_to.")
        return data
