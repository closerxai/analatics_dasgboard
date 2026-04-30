"""
GHL Webhook registration and inbound event handling.

Call register_webhook() once after connecting GHL credentials.
The /api/webhook/ghl/ endpoint calls handle_webhook_event() on every inbound POST.
"""

import logging
import hmac
import hashlib
from typing import Optional

from django.conf import settings

from ..models import Company, Lead, LeadSource, GHLPipelineStage, SyncLog
from .ghl_client import get_ghl_client_for_company, GHLClient
from .ghl_sync import _upsert_opportunity, _get_or_create_source

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────

def register_webhook_for_company(company: Company, webhook_base_url: str) -> str:
    """
    Register a GHL webhook for the given company.
    Returns the webhook_id string.

    webhook_base_url: public base URL of this Django server
                      e.g. "https://api.example.com"
    """
    client = get_ghl_client_for_company(company)
    if not client:
        raise ValueError(f"No GHL credentials for company {company.id}")

    webhook_url = f"{webhook_base_url.rstrip('/')}/api/webhook/ghl/"
    resp = client.register_webhook(webhook_url)
    webhook_id = resp.get("webhook", {}).get("id") or resp.get("id", "")

    # Persist the webhook_id so we can delete it later
    crm = company.crm
    if crm and crm.ghl:
        crm.ghl.webhook_id = webhook_id
        crm.ghl.save(update_fields=["webhook_id"])

    logger.info(f"Registered GHL webhook {webhook_id} for company {company.id}")
    return webhook_id


def deregister_webhook_for_company(company: Company) -> bool:
    """Remove the previously registered webhook. Returns True on success."""
    try:
        crm = company.crm
        if not crm or not crm.ghl or not crm.ghl.webhook_id:
            return False
        client = get_ghl_client_for_company(company)
        if not client:
            return False
        client.delete_webhook(crm.ghl.webhook_id)
        crm.ghl.webhook_id = ""
        crm.ghl.save(update_fields=["webhook_id"])
        return True
    except Exception as e:
        logger.warning(f"Failed to deregister webhook for company {company.id}: {e}")
        return False


# ──────────────────────────────────────────────────
# Signature verification (optional but recommended)
# ──────────────────────────────────────────────────

def verify_ghl_signature(request_body: bytes, signature_header: str, secret: str) -> bool:
    """
    GHL sends X-Webhook-Signature header as HMAC-SHA256 of the body.
    Set GHL_WEBHOOK_SECRET in your .env and Django settings.
    """
    if not secret or not signature_header:
        return True   # skip if not configured
    expected = hmac.new(secret.encode(), request_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ──────────────────────────────────────────────────
# Inbound event handler
# ──────────────────────────────────────────────────

def handle_webhook_event(payload: dict, location_id: str) -> dict:
    """
    Process an inbound GHL webhook event.
    Finds the matching company by location_id and upserts the opportunity/contact.

    Returns a dict with processing result info.
    """
    event_type = payload.get("type") or payload.get("event") or ""
    opp_id = (
        payload.get("id")
        or (payload.get("opportunity") or {}).get("id")
        or ""
    )

    # Resolve company by location_id
    company = _find_company_by_location(location_id)
    if not company:
        logger.warning(f"Webhook received for unknown location_id={location_id}")
        return {"status": "ignored", "reason": "location_id not found"}

    crm = company.crm
    if not crm:
        return {"status": "ignored", "reason": "no CRM configured"}

    # Create a mini sync_log for auditing
    sync_log = SyncLog.objects.create(
        company=company,
        sync_type="webhook",
        status="running",
    )

    try:
        opportunity = _extract_opportunity(payload, event_type)
        if not opportunity:
            sync_log.status = "success"
            sync_log.save()
            return {"status": "ok", "action": "no_opportunity_data"}

        result = _upsert_opportunity(company, crm, opportunity, sync_log)
        sync_log.status = "success"
    except Exception as e:
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        logger.error(f"Webhook processing error: {e}")
        result = "error"

    from django.utils import timezone
    sync_log.completed_at = timezone.now()
    sync_log.save()

    return {
        "status": "ok",
        "event": event_type,
        "opportunity_id": opp_id,
        "action": result,
    }


# ──────────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────────

def _find_company_by_location(location_id: str) -> Optional[Company]:
    from ..models import CRMSecrets
    secret = CRMSecrets.objects.filter(location_id=location_id, name="ghl").first()
    if not secret:
        return None
    try:
        return secret.ghl_crm.company
    except Exception:
        return None


def _extract_opportunity(payload: dict, event_type: str) -> Optional[dict]:
    """Normalize GHL webhook payload into an opportunity dict."""
    et = event_type.lower()

    if "opportunity" in et:
        # Direct opportunity event — payload IS the opportunity (sometimes)
        opp = payload.get("opportunity") or payload
        if opp.get("id"):
            return opp

    if "contact" in et:
        # Contact event — no opportunity data, skip for now
        return None

    # Fallback: check if payload has 'id' that looks like an opportunity
    if payload.get("pipelineId") or payload.get("pipelineStageId"):
        return payload

    return None
