"""
Chicago Commercial Permits DaaS - Data Transformer
===================================================
Cleans raw SODA records, parses nested contacts, standardizes timestamps
to ISO-8601 dates, handles null values, and concatenates standardized addresses.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def parse_iso_date(date_str: Optional[str]) -> Optional[str]:
    """
    Standardize various date formats to ISO-8601 YYYY-MM-DD string.
    Returns None if date_str is empty or unparseable.
    """
    if not date_str or str(date_str).strip().lower() in ("", "none", "null", "n/a"):
        return None
    clean_str = str(date_str).strip()
    # Match ISO format with optional milliseconds/time: YYYY-MM-DD...
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", clean_str)
    if match:
        return match.group(1)
    
    # Try parsing common date formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(clean_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return clean_str[:10] if len(clean_str) >= 10 else clean_str


def build_full_address(record: Dict[str, Any]) -> str:
    """Concatenate street number, direction, and name into a single standardized address."""
    parts = []
    street_num = str(record.get("street_number") or "").strip()
    street_dir = str(record.get("street_direction") or "").strip()
    street_name = str(record.get("street_name") or "").strip()

    if street_num:
        parts.append(street_num)
    if street_dir:
        parts.append(street_dir)
    if street_name:
        parts.append(street_name)

    if not parts:
        return "CHICAGO, IL"
    
    address = " ".join(parts).upper()
    return f"{address}, CHICAGO, IL"


def extract_contacts(record: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Scan dynamic contact fields (contact_1_type, contact_1_name, etc.)
    and identify General Contractor, Owner, and Architect.
    """
    gc_name = None
    owner_name = None
    architect_name = None
    subcontractors = []

    # Check up to 15 possible contact slots in SODA schema
    for i in range(1, 16):
        c_type = str(record.get(f"contact_{i}_type") or "").strip().upper()
        c_name = str(record.get(f"contact_{i}_name") or "").strip()
        if not c_name or c_name.lower() in ("null", "none", "n/a"):
            continue

        if "GENERAL CONTRACTOR" in c_type and not gc_name:
            gc_name = c_name
        elif "OWNER" in c_type and not owner_name:
            owner_name = c_name
        elif "ARCHITECT" in c_type and not architect_name:
            architect_name = c_name
        elif "CONTRACTOR" in c_type:
            subcontractors.append(f"{c_type}: {c_name}")

    # Fallback for general contractor if named simply as GC or first contractor
    if not gc_name and subcontractors:
        gc_name = subcontractors[0]

    return {
        "general_contractor": gc_name or "N/A",
        "owner": owner_name or "N/A",
        "architect": architect_name or "N/A",
        "other_contractors": "; ".join(subcontractors[:3]) if subcontractors else "N/A"
    }


def clean_currency(val: Any) -> float:
    """Safely cast cost/fee strings into float values."""
    if val is None:
        return 0.0
    try:
        clean = re.sub(r"[^\d.]", "", str(val))
        return float(clean) if clean else 0.0
    except (ValueError, TypeError):
        return 0.0


def transform_permit_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a single raw SODA record into a clean, normalized schema."""
    contacts = extract_contacts(raw)
    
    # Cost valuation: use reported_cost or estimated_cost
    raw_cost = raw.get("reported_cost") or raw.get("estimated_cost") or 0.0
    estimated_cost = clean_currency(raw_cost)
    total_fee = clean_currency(raw.get("total_fee"))

    # Descriptions
    work_desc = str(raw.get("work_description") or raw.get("work_type") or "COMMERCIAL ALTERATION / CONSTRUCTION").strip()
    # Normalize unicode dashes and quotes
    work_desc = work_desc.replace("–", "-").replace("—", "-").replace("’", "'").replace("‘", "'")
    work_desc = re.sub(r"\s+", " ", work_desc)

    permit_type = str(raw.get("permit_type") or "PERMIT").strip()
    permit_type = permit_type.replace("–", "-").replace("—", "-")

    return {
        "permit_number": str(raw.get("permit_") or raw.get("id") or "N/A").strip(),
        "issue_date": parse_iso_date(raw.get("issue_date")),
        "application_date": parse_iso_date(raw.get("application_start_date")),
        "estimated_cost": estimated_cost,
        "total_fee": total_fee,
        "address": build_full_address(raw),
        "permit_type": permit_type,
        "work_description": work_desc,
        "general_contractor": contacts["general_contractor"],
        "owner": contacts["owner"],
        "architect": contacts["architect"],
        "subcontractors": contacts["other_contractors"],
        "ward": str(raw.get("ward") or "N/A").strip(),
        "community_area": str(raw.get("community_area") or "N/A").strip(),
        "status": str(raw.get("permit_status") or "ACTIVE").strip(),
    }


def transform_permits(raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform a list of raw SODA permit records."""
    transformed = [transform_permit_record(r) for r in raw_records]
    logger.info(f"Successfully transformed and normalized {len(transformed)} records.")
    return transformed
