from rest_framework import serializers
from .models import Company, Lead, CompanyMember, Role
from django.contrib.auth import get_user_model

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id',
            'company',
            'project',
            'crm',
            'name',
            'email',
            'phone',
            'source',
            'tags',
            'external_id',
            'raw_data',
            'created_at',
            'updated_at',
        ]

User = get_user_model()

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

class CompanyMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = CompanyMember
        fields = ['id', 'username', 'email', 'role', 'role_name', 'is_active', 'joined_at']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_default']

class CompanyMemberCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.IntegerField()

class AssignProjectsSerializer(serializers.Serializer):
    project_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )
