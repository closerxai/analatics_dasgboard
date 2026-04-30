from rest_framework import serializers

from .models import Company, Lead, Project, SyncLog


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "logo", "is_active", "created_at", "updated_at"]


class CompanyAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "logo", "agni_api_key", "is_active", "created_at", "updated_at"]


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "logo", "agni_api_key", "is_active"]


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "logo", "agni_api_key", "is_active"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "external_pipeline_id", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeadSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True, default="")
    project_name = serializers.CharField(source="project.name", read_only=True, default="")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "status",
            "status_display",
            "source",
            "source_name",
            "project",
            "project_name",
            "assigned_to_name",
            "city",
            "planning_for_visit",
            "follow_up_date",
            "whatsapp_status",
            "remarks",
            "monetary_value",
            "ghl_opportunity_id",
            "ghl_pipeline_stage_name",
            "ghl_opportunity_status",
            "external_id",
            "created_at",
            "updated_at",
        ]


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            "project",
            "crm",
            "name",
            "email",
            "phone",
            "source",
            "tags",
            "status",
            "assigned_to_name",
            "city",
            "planning_for_visit",
            "follow_up_date",
            "whatsapp_status",
            "remarks",
            "monetary_value",
            "external_id",
            "raw_data",
        ]


class SyncLogSerializer(serializers.ModelSerializer):
    sync_type_display = serializers.CharField(source="get_sync_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    triggered_by_email = serializers.CharField(source="triggered_by.email", read_only=True, default=None)

    class Meta:
        model = SyncLog
        fields = [
            "id",
            "sync_type",
            "sync_type_display",
            "status",
            "status_display",
            "started_at",
            "completed_at",
            "leads_synced",
            "leads_created",
            "leads_updated",
            "error_message",
            "date_from",
            "date_to",
            "triggered_by_email",
        ]
