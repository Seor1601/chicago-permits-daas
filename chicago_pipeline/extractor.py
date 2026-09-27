"""
Chicago Commercial Permits DaaS - SODA Extractor
=================================================
Fetches high-value commercial building permit data from the City of Chicago
open data portal using SODA (Socrata Open Data API).
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

# Official City of Chicago Building Permits SODA endpoint
SODA_ENDPOINT = "https://data.cityofchicago.org/resource/ydr8-5enu.json"


class PermitExtractor:
    """Extracts building permits from City of Chicago SODA API."""

    def __init__(self, endpoint: str = SODA_ENDPOINT, app_token: Optional[str] = None):
        self.endpoint = endpoint
        self.app_token = app_token or os.environ.get("CHICAGO_SODA_APP_TOKEN")

    def fetch_permits(
        self,
        min_cost: float = 50000.0,
        limit: int = 100,
        order_by: str = "issue_date DESC",
    ) -> List[Dict[str, Any]]:
        """
        Fetch permits exceeding `min_cost` ordered descending by date.
        
        Note on SODA schema: The City of Chicago building permits dataset uses
        `reported_cost` as the column name representing the estimated/reported construction value.
        """
        headers = {
            "Accept": "application/json",
            "User-Agent": "ChicagoCommercialPermitsDaaS/1.0"
        }
        if self.app_token:
            headers["X-App-Token"] = self.app_token

        # In SODA, reported_cost is the official schema column for permit valuation
        where_clause = f"reported_cost >= {int(min_cost)}"

        params = {
            "$where": where_clause,
            "$order": order_by,
            "$limit": limit,
        }

        logger.info(f"Querying SODA API: {self.endpoint} with params: {params}")

        try:
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully retrieved {len(data)} permit records from Chicago SODA API.")
            return data
        except requests.RequestException as e:
            logger.error(f"Error fetching data from SODA API: {e}")
            raise


def extract_commercial_permits(min_cost: float = 50000.0, limit: int = 100) -> List[Dict[str, Any]]:
    """Convenience helper to extract high-value permits."""
    extractor = PermitExtractor()
    return extractor.fetch_permits(min_cost=min_cost, limit=limit)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    records = extract_commercial_permits(min_cost=50000, limit=5)
    print(f"Extracted {len(records)} records. First permit: {records[0].get('permit_')}")
