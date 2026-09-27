"""
Chicago Commercial Permits DaaS - Main CLI Entrypoint
======================================================
Orchestrates the ETL execution:
1. Extraction: queries City of Chicago SODA API for permits >= $50k.
2. Transformation: cleans nulls, standardizes ISO dates, concatenates addresses.
3. Export: compiles styled .xlsx with accounting currency and auto-width columns.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

from chicago_pipeline.extractor import PermitExtractor
from chicago_pipeline.transformer import transform_permits
from chicago_pipeline.exporter import export_to_excel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("chicago_pipeline")


def run_pipeline(
    min_cost: float = 50000.0,
    limit: int = 100,
    output_file: str = "output/chicago_permits_sample.xlsx"
) -> str:
    """Executes the complete Chicago Commercial Permits ETL cycle."""
    logger.info("=" * 60)
    logger.info("STARTING CHICAGO COMMERCIAL PERMITS PIPELINE")
    logger.info(f"Target filter: reported_cost >= ${min_cost:,.2f} | Limit: {limit} records")
    logger.info("=" * 60)

    # 1. Extraction
    extractor = PermitExtractor()
    raw_records = extractor.fetch_permits(min_cost=min_cost, limit=limit)
    if not raw_records:
        logger.warning("No permits returned by the query.")
        return ""

    logger.info(f"[1/3] Extracted {len(raw_records)} records from City of Chicago.")

    # 2. Transformation
    transformed = transform_permits(raw_records)
    logger.info(f"[2/3] Transformed and normalized {len(transformed)} records.")

    # Total commercial valuation metrics
    total_valuation = sum(r.get("estimated_cost", 0.0) for r in transformed)
    logger.info(f"      Total pipeline pipeline project valuation: ${total_valuation:,.2f} USD")

    # 3. Export
    output_path = export_to_excel(transformed, output_filepath=output_file)
    file_size_kb = os.path.getsize(output_path) / 1024
    logger.info(f"[3/3] Export complete: {output_path} ({file_size_kb:.1f} KB)")
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Chicago Commercial Permits DaaS ETL Pipeline")
    parser.add_argument("--min-cost", type=float, default=50000.0, help="Minimum reported cost threshold (USD)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of permits to extract")
    parser.add_argument("--output", type=str, default="output/chicago_permits_sample.xlsx", help="Destination path for .xlsx")

    args = parser.parse_args()
    run_pipeline(min_cost=args.min_cost, limit=args.limit, output_file=args.output)


if __name__ == "__main__":
    main()
