"""
Chicago Commercial Permits DaaS - Excel Exporter
=================================================
Generates high-grade, production-ready .xlsx spreadsheets using openpyxl,
featuring frozen headers, auto-adapted column widths, accounting currency formatting,
and clean modern styling.
"""

import os
import logging
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


def export_to_excel(
    records: List[Dict[str, Any]],
    output_filepath: str = "output/chicago_permits_sample.xlsx"
) -> str:
    """
    Export list of normalized permit dictionaries to a beautifully styled Excel workbook.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Chicago Permits"

    # Ensure grid lines are visible
    ws.views.sheetView[0].showGridLines = True

    # Column definition: (key, header_title, alignment, is_currency, is_number)
    columns = [
        ("permit_number", "Permit #", "center", False, False),
        ("issue_date", "Issue Date", "center", False, False),
        ("application_date", "Applied Date", "center", False, False),
        ("estimated_cost", "Reported Value ($)", "right", True, True),
        ("total_fee", "City Fee ($)", "right", True, True),
        ("address", "Property Address", "left", False, False),
        ("work_description", "Scope of Work", "left", False, False),
        ("general_contractor", "General Contractor", "left", False, False),
        ("owner", "Property Owner", "left", False, False),
        ("architect", "Architect / Design Firm", "left", False, False),
        ("subcontractors", "Key Trade Subcontractors", "left", False, False),
        ("permit_type", "Permit Type", "left", False, False),
        ("ward", "Ward", "center", False, False),
        ("status", "Status", "center", False, False),
    ]

    # Header styling (Linear / Swiss minimal zinc palette)
    header_fill = PatternFill(start_color="09090B", end_color="09090B", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)

    # Data row styling
    regular_font = Font(name="Segoe UI", size=10, color="18181B")
    bold_lead_font = Font(name="Segoe UI", size=10, bold=True, color="09090B")
    
    # Border styles
    thin_border_side = Side(border_style="thin", color="E4E4E7")
    thin_border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side
    )
    
    # Zebra striping
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # Write headers
    for col_idx, (_, header_title, _, _, _) in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=header_title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    ws.row_dimensions[1].height = 26

    # Write data rows
    for row_idx, record in enumerate(records, 2):
        is_even = (row_idx % 2 == 0)
        row_fill = None if is_even else alt_fill

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

            cell.font = bold_lead_font if is_currency else regular_font
            cell.alignment = Alignment(horizontal=h_align, vertical="center")
            cell.border = thin_border
            if row_fill:
                cell.fill = row_fill

        ws.row_dimensions[row_idx].height = 20

    # Freeze header row
    ws.freeze_panes = "A2"

    # Auto-adapt column widths with limits
    for col_idx, (key, header_title, _, _, _) in enumerate(columns, 1):
        max_len = len(header_title)
        for row in range(2, len(records) + 2):
            cell_val = ws.cell(row=row, column=col_idx).value
            if cell_val is not None:
                if key == "estimated_cost" or key == "total_fee":
                    s_len = len(f"${float(cell_val):,.0f}")
                else:
                    s_len = len(str(cell_val))
                if s_len > max_len:
                    max_len = s_len
        
        col_letter = get_column_letter(col_idx)
        # Add safety margin and clamp
        adjusted_width = min(max(max_len + 4, 12), 65)
        ws.column_dimensions[col_letter].width = adjusted_width

    wb.save(output_filepath)
    logger.info(f"Excel workbook successfully saved to: {output_filepath}")
    return output_filepath
