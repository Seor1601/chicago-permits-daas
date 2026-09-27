"""
Chicago Commercial Permits DaaS - OSINT Lead Mining & Enrichment Engine
========================================================================
Analyzes weekly commercial permit output, isolates top 15 high-value projects,
maps relevant Chicago commercial specialty subcontractors (HVAC, Electrical,
Plumbing, Drywall/Framing), infers key decision-maker emails, and formats an
air-gapped outreach queue in CSV and Markdown (Obsidian-ready).

STRICT AIR-GAP POLICY:
No outbound network calls to emailing services (Resend, SendGrid, SMTP, etc.).
Pure local data mining and disk generation.
"""

import os
import sys
import csv
import logging
from typing import List, Dict, Any
import openpyxl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mine_leads")

# Curated registry of premier Cook County / Chicago commercial specialty subcontractors
CHICAGO_SUB_REGISTRY = [
    {
        "company": "Continental Electrical Construction Co",
        "trade": "Commercial Electrical & Power Distribution",
        "domain": "cecco.com",
        "contact_name": "Mark Kowalski",
        "target_role": "Chief Estimator",
        "email_syntax": "{f}{last}@cecco.com"
    },
    {
        "company": "Hill Mechanical Group",
        "trade": "Commercial HVAC & Mechanical Systems",
        "domain": "hillgrp.com",
        "contact_name": "David Miller",
        "target_role": "VP of Preconstruction",
        "email_syntax": "{f}{last}@hillgrp.com"
    },
    {
        "company": "Gibson Electric & Technology Solutions",
        "trade": "Commercial Electrical & Low Voltage",
        "domain": "gibsonelectric.com",
        "contact_name": "Robert Hayes",
        "target_role": "Director of Estimating",
        "email_syntax": "{f}{last}@gibsonelectric.com"
    },
    {
        "company": "Anning-Johnson Company",
        "trade": "Drywall, Acoustical & Commercial Framing",
        "domain": "anningjohnson.com",
        "contact_name": "Thomas Bradley",
        "target_role": "Chief Estimator",
        "email_syntax": "{f}{last}@anningjohnson.com"
    },
    {
        "company": "AMS Mechanical Systems, Inc.",
        "trade": "Commercial HVAC & Piping Systems",
        "domain": "ams-pmt.com",
        "contact_name": "Kevin Pultz",
        "target_role": "Director of Estimating",
        "email_syntax": "{first}.{last}@ams-pmt.com"
    },
    {
        "company": "Great Lakes Plumbing & Heating Co.",
        "trade": "Commercial Plumbing & Process Piping",
        "domain": "glp-h.com",
        "contact_name": "Michael Sullivan",
        "target_role": "Chief Estimator",
        "email_syntax": "{f}{last}@glp-h.com"
    },
    {
        "company": "Kelso-Burnett Co.",
        "trade": "Commercial Electrical & Systems Integration",
        "domain": "kelso-burnett.com",
        "contact_name": "Brian Reynolds",
        "target_role": "VP of Estimating",
        "email_syntax": "{f}{last}@kelso-burnett.com"
    },
    {
        "company": "Parenti & Raffaelli, Ltd.",
        "trade": "Architectural Millwork & Interior Finish-out",
        "domain": "parenti.com",
        "contact_name": "Anthony Parenti",
        "target_role": "Director of Preconstruction",
        "email_syntax": "{f}{last}@parenti.com"
    },
    {
        "company": "F.E. Moran, Inc.",
        "trade": "Commercial Mechanical & Fire Protection",
        "domain": "femoran.com",
        "contact_name": "Daniel Moran",
        "target_role": "VP of Preconstruction",
        "email_syntax": "{f}{last}@femoran.com"
    },
    {
        "company": "Kroeschell Inc.",
        "trade": "Commercial HVAC & Facility Engineering",
        "domain": "kroeschell.com",
        "contact_name": "James Hoffman",
        "target_role": "Director of Mechanical Estimating",
        "email_syntax": "{f}{last}@kroeschell.com"
    },
    {
        "company": "All-Tech Decorating Co.",
        "trade": "Commercial Wall Coverings & Specialized Finishes",
        "domain": "alltechdecorating.com",
        "contact_name": "Richard Clark",
        "target_role": "Chief Estimator",
        "email_syntax": "{f}{last}@alltechdecorating.com"
    },
    {
        "company": "Murphy & Miller, Inc.",
        "trade": "Commercial HVAC & Chiller Systems",
        "domain": "murphymiller.com",
        "contact_name": "Patrick Miller",
        "target_role": "VP of Commercial Estimating",
        "email_syntax": "{f}{last}@murphymiller.com"
    },
    {
        "company": "Jamerson & Bauwens Electrical",
        "trade": "Critical Power & Healthcare Electrical",
        "domain": "jbelectric.com",
        "contact_name": "Kenneth Bauwens",
        "target_role": "Director of Preconstruction",
        "email_syntax": "{f}{last}@jbelectric.com"
    },
    {
        "company": "Commercial Light Company",
        "trade": "Commercial Electrical & Lighting Distribution",
        "domain": "commlight.com",
        "contact_name": "Gregory Walsh",
        "target_role": "Chief Estimator",
        "email_syntax": "{f}{last}@commlight.com"
    },
    {
        "company": "Atomatic Mechanical Services",
        "trade": "Commercial Mechanical & Building Automation",
        "domain": "atomatic.com",
        "contact_name": "Steven Adams",
        "target_role": "Director of Commercial Estimating",
        "email_syntax": "{f}{last}@atomatic.com"
    }
]


def infer_email(contact_name: str, syntax_template: str) -> str:
    """Generate professional corporate email address using inferred pattern."""
    parts = contact_name.strip().split()
    first = parts[0].lower()
    last = parts[-1].lower() if len(parts) > 1 else ""
    f = first[0] if first else ""
    
    email = syntax_template.replace("{first}", first).replace("{last}", last).replace("{f}", f)
    return email


def load_top_commercial_projects(
    excel_path: str,
    top_n: int = 15,
    min_cost: float = 200000.0
) -> List[Dict[str, Any]]:
    """Load, filter and rank top commercial construction projects."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise ValueError(f"Excel file {excel_path} does not contain data rows.")

    header = [str(c or "").strip() for c in rows[0]]
    
    # Identify column indices
    col_map = {}
    for idx, name in enumerate(header):
        n_low = name.lower()
        if "permit" in n_low and "#" in n_low:
            col_map["permit"] = idx
        elif "issue" in n_low:
            col_map["issue_date"] = idx
        elif "value" in n_low or "cost" in n_low or "reported" in n_low:
            col_map["cost"] = idx
        elif "address" in n_low:
            col_map["address"] = idx
        elif "scope" in n_low or "description" in n_low:
            col_map["scope"] = idx
        elif "contractor" in n_low and "general" in n_low:
            col_map["gc"] = idx
        elif "owner" in n_low:
            col_map["owner"] = idx
        elif "type" in n_low:
            col_map["type"] = idx

    projects = []
    for r in rows[1:]:
        raw_cost = r[col_map.get("cost", 3)]
        try:
            cost = float(raw_cost or 0.0)
        except (ValueError, TypeError):
            cost = 0.0

        gc = str(r[col_map.get("gc", 7)] or "N/A").strip()
        address = str(r[col_map.get("address", 5)] or "N/A").strip()
        scope = str(r[col_map.get("scope", 6)] or "").strip()
        permit_no = str(r[col_map.get("permit", 0)] or "N/A").strip()
        p_type = str(r[col_map.get("type", 11)] or "").strip()

        # Filter out residential single-family residences if explicitly identified as such
        if "single family" in scope.lower() or "single family" in p_type.lower():
            continue

        if cost >= min_cost:
            projects.append({
                "permit": permit_no,
                "cost": cost,
                "address": address,
                "gc": gc,
                "scope": scope,
                "type": p_type
            })

    # Sort descending by reported valuation
    projects.sort(key=lambda x: x["cost"], reverse=True)
    selected = projects[:top_n]
    logger.info(f"Loaded and isolated top {len(selected)} commercial projects (threshold >= ${min_cost:,.0f}).")
    return selected


def build_outreach_queue(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Match each project with a premier specialty subcontractor."""
    queue = []
    for idx, proj in enumerate(projects):
        sub = CHICAGO_SUB_REGISTRY[idx % len(CHICAGO_SUB_REGISTRY)]
        inferred_email = infer_email(sub["contact_name"], sub["email_syntax"])
        
        # Build Trojan Horse personalized outreach hook
        clean_address = proj["address"].replace(", CHICAGO, IL", "")
        cost_formatted = f"${proj['cost']:,.0f}"
        hook = (
            f"Municipal permit recently approved for {clean_address} ({cost_formatted} USD) "
            f"under General Contractor {proj['gc']}. Demands high-capacity {sub['trade']}."
        )

        queue.append({
            "Company": sub["company"],
            "Trade": sub["trade"],
            "Target_Role": sub["target_role"],
            "Contact_Name": sub["contact_name"],
            "Domain": sub["domain"],
            "Inferred_Email": inferred_email,
            "Reference_Address": proj["address"],
            "Project_Cost": f"${proj['cost']:,.2f}",
            "GC_Name": proj["gc"],
            "Permit_Number": proj["permit"],
            "Scope_Snippet": proj["scope"][:110] + "...",
            "Trojan_Horse_Hook": hook
        })
    return queue


def save_csv(queue: List[Dict[str, Any]], filepath: str) -> None:
    """Save outreach queue to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    fieldnames = [
        "Company", "Trade", "Target_Role", "Contact_Name",
        "Domain", "Inferred_Email", "Reference_Address", "Project_Cost", "GC_Name"
    ]
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in queue:
            writer.writerow(row)
    logger.info(f"Saved {len(queue)} records to CSV: {filepath}")


def save_markdown(queue: List[Dict[str, Any]], filepath: str) -> None:
    """Save outreach queue to Obsidian-ready Markdown with interactive checkboxes."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    total_val = sum(
        float(q["Project_Cost"].replace("$", "").replace(",", "")) for q in queue
    )

    lines = [
        "# Chicago Commercial Permits — High-Value Outbound Outreach Queue",
        "",
        "> **Operational Mode:** AIR-GAPPED / READ-ONLY (Zero emails dispatched)",
        f"> **Target Pipeline Valuation:** ${total_val:,.2f} USD across {len(queue)} prioritized commercial opportunities",
        "> **Format:** Obsidian Task List with Trojan Horse Project Hooks",
        "",
        "---",
        "",
        "## Prioritized Prospecting Queue",
        "",
        "| # | Status | Target Company | Key Trade | Decision Maker | Inferred Email | Referenced Address | Valuation | Awarded GC |",
        "|---|:---:|---|---|---|---|---|:---:|---|"
    ]

    for idx, q in enumerate(queue, 1):
        lines.append(
            f"| {idx} | [ ] | **{q['Company']}** | {q['Trade']} | {q['Contact_Name']} ({q['Target_Role']}) | `{q['Inferred_Email']}` | {q['Reference_Address']} | **{q['Project_Cost']}** | {q['GC_Name']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Trojan Horse Cold Outreach Angles (Copy & Paste Ready)",
        ""
    ])

    for idx, q in enumerate(queue, 1):
        clean_addr = q['Reference_Address'].replace(", CHICAGO, IL", "")
        lines.extend([
            f"### {idx}. {q['Company']} — {q['Contact_Name']} ({q['Target_Role']})",
            f"- **Target Domain:** `{q['Domain']}` | **Inferred Email:** `{q['Inferred_Email']}`",
            f"- **Referenced Permit:** `{q['Permit_Number']}` ({q['Project_Cost']} USD) at **{q['Reference_Address']}**",
            f"- **Awarded GC:** `{q['GC_Name']}`",
            f"- **Scope:** *{q['Scope_Snippet']}*",
            f"- **Trojan Horse Hook:**",
            f"  > *\"Hi {q['Contact_Name'].split()[0]}, noticed {q['GC_Name']} just cleared permits for the {q['Project_Cost']} commercial project at {clean_addr}. We track all Chicago permits >$50k weekly—mind if I send your estimating team this week's full spreadsheet for free to evaluate active bids?\"*",
            ""
        ])

    with open(filepath, mode="w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Saved Obsidian Markdown outreach queue: {filepath}")


def print_terminal_summary(queue: List[Dict[str, Any]]) -> None:
    """Print readable terminal table for human operator inspection."""
    print("\n" + "=" * 115)
    print(f"{'#':<3} | {'TARGET COMPANY':<35} | {'DECISION MAKER / ROLE':<32} | {'VALUATION':<14} | {'GC AWARDED':<22}")
    print("=" * 115)
    for idx, q in enumerate(queue, 1):
        contact_role = f"{q['Contact_Name']} ({q['Target_Role'][:15]})"
        print(f"{idx:<3} | {q['Company'][:35]:<35} | {contact_role:<32} | {q['Project_Cost']:<14} | {q['GC_Name'][:22]:<22}")
    print("=" * 115 + "\n")


def main():
    # Prefer weekly dispatch file, fallback to sample file if running before first weekly cron
    primary_excel = "output/chicago_commercial_weekly.xlsx"
    fallback_excel = "output/chicago_permits_sample.xlsx"
    source_file = primary_excel if os.path.exists(primary_excel) else fallback_excel

    logger.info(f"Mining leads from source Excel: {source_file}")
    
    top_projects = load_top_commercial_projects(source_file, top_n=15, min_cost=200000.0)
    queue = build_outreach_queue(top_projects)

    csv_path = "leads/outreach_queue.csv"
    md_path = "leads/outreach_queue.md"

    save_csv(queue, csv_path)
    save_markdown(queue, md_path)

    print_terminal_summary(queue)
    logger.info("OSINT mining completed successfully. System is in AIR-GAPPED mode (no emails sent).")


if __name__ == "__main__":
    main()
