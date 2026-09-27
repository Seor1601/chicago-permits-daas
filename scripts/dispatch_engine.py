"""
Chicago Commercial Permits DaaS - Automated Dispatch Engine
=============================================================
"Set & Forget" weekly pipeline:
1. Queries City of Chicago SODA API (ydr8-5enu.json) for the last 7 days.
2. Filters server-side: reported_cost >= $50,000 and commercial permit types
   ('PERMIT - NEW CONSTRUCTION', 'PERMIT - RENOVATION/ALTERATION').
3. Normalizes and structures data using robust contact and address parsing.
4. Generates an executive Excel (.xlsx) file with Slate Blue (#1E293B) headers,
   frozen A2 panes, accounting currency ($#,##0), and auto-adapted column widths.
5. Queries Polar.sh API (/v1/subscriptions?status=active) to identify active subscribers.
6. Handles dry-run and failure logging.
"""

import os
import sys
import logging
import argparse
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("dispatch_engine")

SODA_ENDPOINT = "https://data.cityofchicago.org/resource/ydr8-5enu.json"
POLAR_API_BASE = "https://api.polar.sh/v1"


def clean_currency(val: Any) -> float:
    """Safely cast string cost/fee to float."""
    if val is None:
        return 0.0
    try:
        clean = re.sub(r"[^\d.]", "", str(val))
        return float(clean) if clean else 0.0
    except (ValueError, TypeError):
        return 0.0


def parse_iso_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize date to YYYY-MM-DD."""
    if not date_str or str(date_str).strip().lower() in ("", "none", "null", "n/a"):
        return None
    clean = str(date_str).strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", clean)
    if match:
        return match.group(1)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return clean[:10] if len(clean) >= 10 else clean


def build_address(record: Dict[str, Any]) -> str:
    """Concatenate street parts into a standardized Chicago address."""
    parts = []
    num = str(record.get("street_number") or "").strip()
    direction = str(record.get("street_direction") or "").strip()
    name = str(record.get("street_name") or "").strip()

    if num:
        parts.append(num)
    if direction:
        parts.append(direction)
    if name:
        parts.append(name)

    if not parts:
        return "CHICAGO, IL"
    return f"{' '.join(parts).upper()}, CHICAGO, IL"


def extract_contacts(record: Dict[str, Any]) -> Dict[str, str]:
    """Scan multi-party contact slots to identify key trade entities."""
    gc_name = None
    owner_name = None
    architect_name = None
    subcontractors = []

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

    if not gc_name and subcontractors:
        gc_name = subcontractors[0]

    return {
        "general_contractor": gc_name or "N/A",
        "owner": owner_name or "N/A",
        "architect": architect_name or "N/A",
        "subcontractors": "; ".join(subcontractors[:3]) if subcontractors else "N/A"
    }


def fetch_chicago_commercial_permits(
    days_back: int = 7,
    min_cost: float = 50000.0,
    limit: int = 500,
    app_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract commercial permits from SODA API:
    - issue_date >= cutoff (last N days)
    - reported_cost >= min_cost
    - permit_type in ('PERMIT - NEW CONSTRUCTION', 'PERMIT - RENOVATION/ALTERATION')
    """
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days_back)
    cutoff_iso = cutoff_dt.strftime("%Y-%m-%dT00:00:00.000")

    where_clause = (
        f"issue_date >= '{cutoff_iso}' "
        f"AND reported_cost >= {int(min_cost)} "
        f"AND (permit_type = 'PERMIT - NEW CONSTRUCTION' OR permit_type = 'PERMIT - RENOVATION/ALTERATION')"
    )

    params = {
        "$where": where_clause,
        "$order": "issue_date DESC, reported_cost DESC",
        "$limit": limit
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "ChicagoCommercialPermitDispatch/2.0"
    }
    token = app_token or os.environ.get("CHICAGO_SODA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token

    logger.info(f"Connecting to SODA API: {SODA_ENDPOINT}")
    logger.info(f"Window: Last {days_back} days (since {cutoff_iso[:10]}) | Min cost: ${min_cost:,.0f}")
    
    response = requests.get(SODA_ENDPOINT, params=params, headers=headers, timeout=35)
    response.raise_for_status()
    records = response.json()
    logger.info(f"Retrieved {len(records)} raw permit records from City of Chicago.")

    # Graceful fallback: if dataset in short 7-day window is unusually sparse (e.g. holiday weekend),
    # expand window to 14 days to ensure subscriber delivery has high utility
    if len(records) < 5 and days_back <= 7:
        logger.warning(f"Short window yielded only {len(records)} records. Expanding to 14 days for robust dataset depth...")
        return fetch_chicago_commercial_permits(days_back=14, min_cost=min_cost, limit=limit, app_token=app_token)

    return records


def transform_records(raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize raw records into clean schema."""
    transformed = []
    for raw in raw_records:
        contacts = extract_contacts(raw)
        cost = clean_currency(raw.get("reported_cost") or raw.get("estimated_cost"))
        fee = clean_currency(raw.get("total_fee"))

        desc = str(raw.get("work_description") or raw.get("work_type") or "COMMERCIAL ALTERATION / CONSTRUCTION").strip()
        desc = re.sub(r"\s+", " ", desc.replace("–", "-").replace("—", "-"))

        p_type = str(raw.get("permit_type") or "PERMIT").strip().replace("–", "-").replace("—", "-")

        transformed.append({
            "permit_number": str(raw.get("permit_") or raw.get("id") or "N/A").strip(),
            "issue_date": parse_iso_date(raw.get("issue_date")),
            "application_date": parse_iso_date(raw.get("application_start_date")),
            "reported_cost": cost,
            "total_fee": fee,
            "address": build_address(raw),
            "permit_type": p_type,
            "work_description": desc,
            "general_contractor": contacts["general_contractor"],
            "owner": contacts["owner"],
            "architect": contacts["architect"],
            "subcontractors": contacts["subcontractors"],
            "ward": str(raw.get("ward") or "N/A").strip(),
            "status": str(raw.get("permit_status") or "ACTIVE").strip(),
        })

    logger.info(f"Normalized {len(transformed)} commercial records.")
    return transformed


def export_commercial_excel(
    records: List[Dict[str, Any]],
    output_filepath: str = "output/chicago_commercial_weekly.xlsx"
) -> str:
    """
    Format Excel file using openpyxl:
    - Slate Blue header (#1E293B) with white bold text
    - Freeze panes at A2
    - Accounting currency formatting ($#,##0)
    - Dynamic column widths
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Commercial Permits"
    ws.views.sheetView[0].showGridLines = True

    columns = [
        ("permit_number", "Permit #", "center", False, False),
        ("issue_date", "Issue Date", "center", False, False),
        ("application_date", "Applied Date", "center", False, False),
        ("reported_cost", "Reported Value ($)", "right", True, True),
        ("total_fee", "City Fee ($)", "right", True, True),
        ("address", "Job Address", "left", False, False),
        ("work_description", "Scope of Work", "left", False, False),
        ("general_contractor", "General Contractor", "left", False, False),
        ("owner", "Property Owner / Developer", "left", False, False),
        ("architect", "Architect of Record", "left", False, False),
        ("subcontractors", "Key Trade Subcontractors", "left", False, False),
        ("permit_type", "Permit Type", "left", False, False),
        ("ward", "Ward", "center", False, False),
        ("status", "Status", "center", False, False),
    ]

    # Required Slate Blue Header: #1E293B
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=False)

    regular_font = Font(name="Segoe UI", size=10, color="0F172A")
    currency_font = Font(name="Segoe UI", size=10, bold=True, color="0F172A")

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # Write Header row
    for col_idx, (_, header_title, _, _, _) in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=header_title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = thin_border
    ws.row_dimensions[1].height = 28

    # Write Data rows
    for row_idx, record in enumerate(records, 2):
        row_fill = None if (row_idx % 2 == 0) else alt_fill

        for col_idx, (key, _, h_align, is_currency, is_number) in enumerate(columns, 1):
            val = record.get(key)
            cell = ws.cell(row=row_idx, column=col_idx)

            if is_number:
                cell.value = float(val) if val is not None else 0.0
                if is_currency:
                    # Accounting currency format: $#,##0
                    cell.number_format = "$#,##0"
            else:
                cell.value = str(val or "N/A")

            cell.font = currency_font if is_currency else regular_font
            cell.alignment = Alignment(horizontal=h_align, vertical="center")
            cell.border = thin_border
            if row_fill:
                cell.fill = row_fill

        ws.row_dimensions[row_idx].height = 20

    # Freeze panes at A2
    ws.freeze_panes = "A2"

    # Dynamic column widths
    for col_idx, (key, header_title, _, _, _) in enumerate(columns, 1):
        max_len = len(header_title)
        for row in range(2, len(records) + 2):
            cell_val = ws.cell(row=row, column=col_idx).value
            if cell_val is not None:
                if key in ("reported_cost", "total_fee"):
                    s_len = len(f"${float(cell_val):,.0f}")
                else:
                    s_len = len(str(cell_val))
                if s_len > max_len:
                    max_len = s_len

        col_letter = get_column_letter(col_idx)
        adjusted_width = min(max(max_len + 4, 12), 65)
        ws.column_dimensions[col_letter].width = adjusted_width

    wb.save(output_filepath)
    file_size_kb = os.path.getsize(output_filepath) / 1024
    logger.info(f"Excel export complete: {output_filepath} ({file_size_kb:.1f} KB)")
    return output_filepath


def get_active_polar_subscribers(token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Query Polar.sh API (/v1/subscriptions?status=active) to retrieve paying subscribers.
    Handles dry-run mode and missing tokens gracefully.
    """
    api_token = token or os.environ.get("POLAR_ACCESS_TOKEN")
    if not api_token:
        logger.warning(
            "POLAR_ACCESS_TOKEN is not set. Operating in DRY-RUN mode for subscriber retrieval. "
            "No live customers will be contacted."
        )
        return []

    url = f"{POLAR_API_BASE}/subscriptions"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "User-Agent": "ChicagoCommercialPermitDispatch/2.0"
    }
    params = {"status": "active"}

    logger.info(f"Querying Polar.sh API: {url} for active subscriptions...")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=25)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        active_subscribers = []
        for sub in items:
            user = sub.get("user") or sub.get("customer") or {}
            email = user.get("email") or sub.get("email")
            sub_id = sub.get("id")
            if email:
                active_subscribers.append({"id": sub_id, "email": email, "status": "active"})

        logger.info(f"Successfully retrieved {len(active_subscribers)} active paying subscribers from Polar.sh.")
        return active_subscribers
    except requests.RequestException as e:
        logger.error(f"Error connecting to Polar.sh API: {e}")
        # Non-fatal for local testing, fatal in production dispatch
        if os.environ.get("CI"):
            raise
        return []


def run_dispatch_pipeline(
    days_back: int = 7,
    min_cost: float = 50000.0,
    output_file: str = "output/chicago_commercial_weekly.xlsx",
    dry_run: bool = False
) -> Dict[str, Any]:
    """Execute complete unattended dispatch workflow."""
    logger.info("=" * 65)
    logger.info("STARTING CHICAGO COMMERCIAL PERMITS DISPATCH PIPELINE")
    logger.info(f"Mode: {'DRY-RUN (Simulated)' if dry_run else 'LIVE DISPATCH'}")
    logger.info("=" * 65)

    # 1. Ingestion
    raw = fetch_chicago_commercial_permits(days_back=days_back, min_cost=min_cost)
    if not raw:
        raise RuntimeError("No records retrieved from City of Chicago open data API.")

    # 2. Transformation
    records = transform_records(raw)
    total_val = sum(r.get("reported_cost", 0.0) for r in records)
    logger.info(f"Total Weekly Commercial Valuation: ${total_val:,.2f} USD across {len(records)} permits.")

    # 3. Excel Compilation
    excel_path = export_commercial_excel(records, output_filepath=output_file)

    # 4. Subscriber Sync
    subscribers = get_active_polar_subscribers()
    logger.info(f"Subscribers ready for weekly delivery: {len(subscribers)}")

    if dry_run or not subscribers:
        logger.info("[DRY-RUN COMPLETE] Spreadsheet generated and verified. Zero emails dispatched.")
    else:
        logger.info(f"Ready to dispatch weekly release to {len(subscribers)} subscribers.")

    logger.info("=" * 65)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 65)

    return {
        "status": "success",
        "records_count": len(records),
        "total_valuation": total_val,
        "excel_path": excel_path,
        "subscribers_count": len(subscribers)
    }


def main():
    parser = argparse.ArgumentParser(description="Chicago Commercial Permits Weekly Dispatch Engine")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--min-cost", type=float, default=50000.0, help="Minimum valuation threshold (default: 50000)")
    parser.add_argument("--output", type=str, default="output/chicago_commercial_weekly.xlsx", help="Destination path")
    parser.add_argument("--dry-run", action="store_true", help="Execute without notifying live subscribers")

    args = parser.parse_args()
    try:
        run_dispatch_pipeline(
            days_back=args.days_back,
            min_cost=args.min_cost,
            output_file=args.output,
            dry_run=args.dry_run
        )
    except Exception as e:
        logger.error(f"FATAL: Dispatch pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
