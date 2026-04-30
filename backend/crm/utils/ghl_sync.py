"""
GHL Sync utilities.

Three sync modes:
  1. auto_sync()    — called every 1 hour, pulls data from last 1.5 hours
  2. manual_sync()  — user-triggered with explicit start/end date
  3. (webhook)      — handled in ghl_webhook.py

All modes call _upsert_opportunity() which is idempotent.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from django.utils import timezone as dj_timezone

from ..models import (
    Company, CRM, Lead, LeadSource, Project,
    GHLPipelineStage, SyncLog, CompanyMember,
)
from .ghl_client import GHLClient, get_ghl_client_for_company

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────

def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _get_or_create_source(name: str) -> Optional[LeadSource]:
    if not name:
        return None
    source, _ = LeadSource.objects.get_or_create(name=name[:100])
    return source


def _map_ghl_status_to_local(ghl_status: str, stage_name: str = "") -> str:
    """
    GHL opportunity status: open | won | lost | abandoned
    Map to our LEAD_STATUS_CHOICES + stage-based heuristics.
    """
    if ghl_status == "won":
        return "site_visit_done"
    if ghl_status in ("lost", "abandoned"):
        return "disqualified"

    # For "open" we use stage name heuristics
    sn = (stage_name or "").lower()
    if "site visit done" in sn or "visit done" in sn:
        return "site_visit_done"
    if "site visit" in sn or "visit booked" in sn or "book" in sn:
        return "booked_site_visit"
    if "callback" in sn or "call back" in sn:
        return "call_back"
    if "qualified" in sn and "dis" not in sn:
        return "qualified"
    if "disqualified" in sn or "not interested" in sn:
        return "disqualified"
    if "not responding" in sn or "no response" in sn:
        return "not_responding"
    if "whatsapp" in sn or "wa " in sn:
        return "whatsapp"
    return "uncontacted"


def _upsert_opportunity(company: Company, crm: CRM, opp: dict, sync_log: SyncLog) -> str:
    """
    Create or update a Lead from a GHL opportunity dict.
    Returns 'created' or 'updated'.
    """
    opp_id = opp.get("id", "")
    contact = opp.get("contact") or {}
    contact_id = opp.get("contactId") or contact.get("id", "")

    # Basic fields
    name = (
        opp.get("name")
        or contact.get("name")
        or f"Lead {opp_id[:8]}"
    )
    email = contact.get("email") or opp.get("email")
    phone = contact.get("phone") or opp.get("phone")
    source_name = opp.get("source") or contact.get("source") or ""
    assigned_to = opp.get("assignedTo") or ""
    city = ""
    # Try to extract city from custom fields
    for cf in (contact.get("customFields") or []):
        fn = (cf.get("fieldKey") or cf.get("name") or "").lower()
        if "city" in fn:
            city = str(cf.get("fieldValue") or "")[:100]
            break

    monetary_value = opp.get("monetaryValue") or 0
    pipeline_id = opp.get("pipelineId", "")
    stage_id = opp.get("pipelineStageId", "")
    stage_name = opp.get("pipelineStageName", "")
    ghl_status = opp.get("status", "open")
    local_status = _map_ghl_status_to_local(ghl_status, stage_name)

    # Source
    source_obj = _get_or_create_source(source_name)

    # Project — match by pipeline_id
    project = None
    try:
        project = Project.objects.filter(
            company=company,
            external_pipeline_id=pipeline_id,
        ).first()
    except Exception:
        pass

    # Cache pipeline stage
    if pipeline_id and stage_id and stage_name:
        GHLPipelineStage.objects.update_or_create(
            company=company,
            stage_id=stage_id,
            defaults={
                "pipeline_id": pipeline_id,
                "pipeline_name": opp.get("pipelineName", ""),
                "stage_name": stage_name,
                "position": opp.get("stagePosition", 0) or 0,
                "project": project,
            },
        )

    # Upsert Lead
    lead, created = Lead.objects.update_or_create(
        company=company,
        ghl_opportunity_id=opp_id,
        defaults={
            "crm": crm,
            "project": project,
            "name": name[:255],
            "email": email,
            "phone": (phone or "")[:20],
            "source": source_obj,
            "external_id": contact_id,
            "ghl_contact_id": contact_id,
            "ghl_pipeline_id": pipeline_id,
            "ghl_pipeline_stage_id": stage_id,
            "ghl_pipeline_stage_name": stage_name,
            "ghl_opportunity_status": ghl_status,
            "status": local_status,
            "assigned_to_name": (assigned_to or "")[:255],
            "city": city,
            "monetary_value": monetary_value if monetary_value else None,
            "raw_data": opp,
        },
    )

    if created:
        sync_log.leads_created += 1
    else:
        sync_log.leads_updated += 1
    sync_log.leads_synced += 1

    return "created" if created else "updated"


def _run_sync(company: Company, client: GHLClient, crm: CRM,
              date_from: Optional[datetime], date_to: Optional[datetime],
              sync_type: str, triggered_by=None) -> SyncLog:
    """Core sync runner."""
    sync_log = SyncLog.objects.create(
        company=company,
        sync_type=sync_type,
        status="running",
        date_from=date_from,
        date_to=date_to,
        triggered_by=triggered_by,
    )

    try:
        date_from_iso = _iso(date_from) if date_from else None
        date_to_iso = _iso(date_to) if date_to else None

        # Fetch all pipelines for this location and sync each
        pipelines_resp = client.get_pipelines()
        pipelines = pipelines_resp.get("pipelines", [])

        if not pipelines:
            # No pipeline list — sync without pipeline filter
            opportunities = client.get_all_opportunities(
                date_added_gte=date_from_iso,
                date_added_lte=date_to_iso,
            )
            for opp in opportunities:
                try:
                    _upsert_opportunity(company, crm, opp, sync_log)
                except Exception as e:
                    logger.warning(f"Failed to upsert opp {opp.get('id')}: {e}")
        else:
            for pipeline in pipelines:
                pipeline_id = pipeline.get("id")
                opportunities = client.get_all_opportunities(
                    pipeline_id=pipeline_id,
                    date_added_gte=date_from_iso,
                    date_added_lte=date_to_iso,
                )
                for opp in opportunities:
                    try:
                        _upsert_opportunity(company, crm, opp, sync_log)
                    except Exception as e:
                        logger.warning(f"Failed to upsert opp {opp.get('id')}: {e}")

        sync_log.status = "success"
    except Exception as e:
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        logger.error(f"GHL sync failed for company {company.id}: {e}")

    sync_log.completed_at = dj_timezone.now()
    sync_log.save()
    return sync_log


# ──────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────

def auto_sync_company(company: Company) -> Optional[SyncLog]:
    """
    Auto-sync: pull leads from the last 1.5 hours.
    Designed to be called by the scheduler every 1 hour.
    """
    client = get_ghl_client_for_company(company)
    if not client:
        logger.warning(f"No GHL credentials for company {company.id}, skipping auto-sync.")
        return None

    crm = company.crm
    now = dj_timezone.now()
    date_from = now - timedelta(hours=1, minutes=30)

    logger.info(f"[AUTO SYNC] Company={company.name} from={date_from.isoformat()}")
    return _run_sync(company, client, crm, date_from, now, sync_type="auto")


def auto_sync_all():
    """Called by the scheduler every hour. Syncs all active companies with GHL configured."""
    companies = Company.objects.filter(
        is_active=True,
        crm__ghl__isnull=False,
    ).select_related("crm__ghl")

    for company in companies:
        try:
            auto_sync_company(company)
        except Exception as e:
            logger.error(f"auto_sync_all error for company {company.id}: {e}")


def manual_sync_company(
    company: Company,
    date_from: datetime,
    date_to: datetime,
    triggered_by=None,
) -> SyncLog:
    """
    Manual sync triggered by the user with an explicit date range.
    """
    client = get_ghl_client_for_company(company)
    if not client:
        raise ValueError(f"No GHL credentials configured for company '{company.name}'")

    crm = company.crm
    logger.info(f"[MANUAL SYNC] Company={company.name} from={date_from.isoformat()} to={date_to.isoformat()}")
    return _run_sync(company, client, crm, date_from, date_to,
                     sync_type="manual", triggered_by=triggered_by)
