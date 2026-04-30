"""
GoHighLevel (GHL) API v2 client.

Handles authentication and all HTTP calls to the GHL API.
Only used for GHL — Salesforce / Zoho are not supported yet.
"""

import requests
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"


class GHLClient:
    """Thin wrapper around the GHL REST API."""

    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None, location_id: Optional[str] = None):
        self.api_key = api_key
        self.access_token = access_token
        self.location_id = location_id

    def _headers(self) -> Dict[str, str]:
        token = self.access_token or self.api_key
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Version": GHL_API_VERSION,
        }
        return headers

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{GHL_BASE_URL}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: Dict) -> Dict:
        url = f"{GHL_BASE_URL}{path}"
        resp = requests.post(url, headers=self._headers(), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> Dict:
        url = f"{GHL_BASE_URL}{path}"
        resp = requests.delete(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ──────────────────────────────────────────────────
    # Opportunities
    # ──────────────────────────────────────────────────

    def get_opportunities(
        self,
        pipeline_id: Optional[str] = None,
        date_added_gte: Optional[str] = None,
        date_added_lte: Optional[str] = None,
        limit: int = 100,
        start_after: Optional[str] = None,
    ) -> Dict:
        """
        Search opportunities for a location.
        https://highlevel.stoplight.io/docs/integrations/b3A6MjMwOTQ4NzE-search-opportunity
        """
        params: Dict[str, Any] = {
            "location_id": self.location_id,
            "limit": limit,
        }
        if pipeline_id:
            params["pipeline_id"] = pipeline_id
        if date_added_gte:
            params["date"] = date_added_gte   # GHL uses "date" param for gte filter
            params["endDate"] = date_added_lte or ""
        if start_after:
            params["startAfter"] = start_after

        return self._get("/opportunities/search", params)

    def get_all_opportunities(
        self,
        pipeline_id: Optional[str] = None,
        date_added_gte: Optional[str] = None,
        date_added_lte: Optional[str] = None,
    ) -> List[Dict]:
        """Auto-paginate through all opportunities matching the criteria."""
        results = []
        start_after = None

        while True:
            resp = self.get_opportunities(
                pipeline_id=pipeline_id,
                date_added_gte=date_added_gte,
                date_added_lte=date_added_lte,
                limit=100,
                start_after=start_after,
            )
            opportunities = resp.get("opportunities", [])
            results.extend(opportunities)

            meta = resp.get("meta", {})
            next_page_url = meta.get("nextPageUrl")
            if not next_page_url or not opportunities:
                break

            # Extract startAfter from meta
            start_after = meta.get("startAfter") or meta.get("startAfterId")
            if not start_after:
                break

        return results

    def get_opportunity(self, opportunity_id: str) -> Dict:
        return self._get(f"/opportunities/{opportunity_id}")

    # ──────────────────────────────────────────────────
    # Pipelines
    # ──────────────────────────────────────────────────

    def get_pipelines(self) -> Dict:
        """List all pipelines for the location."""
        return self._get("/opportunities/pipelines", params={"locationId": self.location_id})

    # ──────────────────────────────────────────────────
    # Contacts
    # ──────────────────────────────────────────────────

    def get_contact(self, contact_id: str) -> Dict:
        return self._get(f"/contacts/{contact_id}")

    # ──────────────────────────────────────────────────
    # Webhooks
    # ──────────────────────────────────────────────────

    def register_webhook(self, webhook_url: str) -> Dict:
        """Register a webhook for OpportunityCreated and OpportunityUpdated events."""
        data = {
            "locationId": self.location_id,
            "url": webhook_url,
            "name": "Emperium Analytics Auto-Sync",
            "events": [
                "OpportunityCreated",
                "OpportunityUpdated",
                "OpportunityStageUpdate",
                "OpportunityStatusUpdate",
                "ContactCreated",
                "ContactUpdated",
            ],
        }
        return self._post("/webhooks/", data)

    def delete_webhook(self, webhook_id: str) -> Dict:
        return self._delete(f"/webhooks/{webhook_id}")

    def list_webhooks(self) -> Dict:
        return self._get("/webhooks/", params={"locationId": self.location_id})


def get_ghl_client_for_company(company) -> Optional[GHLClient]:
    """
    Returns a GHLClient for the given company's GHL credentials,
    or None if not configured.
    """
    try:
        crm = company.crm
        if not crm or not crm.ghl:
            return None
        secret = crm.ghl
        return GHLClient(
            api_key=secret.api_key,
            access_token=secret.access_token,
            location_id=secret.location_id,
        )
    except Exception:
        return None
