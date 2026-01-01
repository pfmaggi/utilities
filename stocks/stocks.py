#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pypdf>=3.0.0",
# ]
# ///

"""
MIT License

Copyright (c) 2025 Pietro F. Maggi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import csv
import logging
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Pattern

import pypdf

# --- Configuration & Constants ---
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Compile regex patterns once for performance.
# Using named groups could further improve readability if logic gets complex.
RE_AWARD_DATE: Pattern = re.compile(r".*Award.?Date: (\d{2}-\w{3}-\d{4})")
RE_AWARD_ID: Pattern = re.compile(r".*Award.?ID: (C\d{6,7})")
RE_RELEASE_DATE: Pattern = re.compile(r".*Release.?Date: (\d{2}-\w{3}-\d{4})")
RE_VEST_PRICE: Pattern = re.compile(r".*FMV.?@.?Vest: (\$\d?,?\d{2,3}.\d{4})")
RE_QTY_RELEASED: Pattern = re.compile(r".*Quantity.?Released: (\d{1,3}\.\d{4}\s?)")
RE_QTY_NET: Pattern = re.compile(r".*Net.?Quantity: (\d{1,3}\.\d{4}\s?)")

SPLIT_DATE = datetime(2022, 7, 15)
SPLIT_FACTOR = 20.0


class StockData(NamedTuple):
    """Immutable data structure for parsed stock report info."""

    award_date: str
    award_id: str
    release_date: str
    vest_price: str
    quantity_released: str
    quantity_net: str


class PDFParsingError(Exception):
    """Custom exception for failing to parse expected fields in PDF."""

    pass


def organize_report(
    release_date_str: str, award_id: str, original_path: Path, output_dir: Path
) -> None:
    """
    Moves and renames the report into a Year-based directory structure.
    """
    try:
        release_dt = datetime.strptime(release_date_str, "%Y/%m/%d")
        year_folder = output_dir / str(release_dt.year)
        year_folder.mkdir(parents=True, exist_ok=True)

        new_filename = (
            f"{release_dt.strftime('%Y%m%d')} - Release Confirm - {award_id}.pdf"
        )
        new_filepath = year_folder / new_filename

        # Use replace() which is atomic on modern POSIX, unlike os.rename
        original_path.replace(new_filepath)
        logger.debug(f"Moved: {original_path} -> {new_filepath}")

    except (ValueError, OSError) as e:
        logger.error(f"Failed to organize report {original_path}: {e}")


def extract_field(pattern: Pattern, content: str, field_name: str) -> str:
    """Helper to extract regex match or raise a specific error."""
    match = pattern.search(content)
    if not match:
        raise PDFParsingError(f"Could not find '{field_name}' in content.")
    return match.group(1).strip()


def parse_pdf(pdf_path: Path) -> StockData | None:
    """
    Parse a single PDF file and return extracted data.
    Returns None if parsing fails, to allow the main loop to continue.
    """
    try:
        # pypdf is the modern replacement for PyPDF2
        with pdf_path.open("rb") as f:
            reader = pypdf.PdfReader(f)
            if not reader.pages:
                raise PDFParsingError("PDF is empty.")
            content = reader.pages[0].extract_text()

        # Extract raw strings
        raw_award_date = extract_field(RE_AWARD_DATE, content, "Award Date")
        award_id = extract_field(RE_AWARD_ID, content, "Award ID")
        raw_release_date = extract_field(RE_RELEASE_DATE, content, "Release Date")
        vest_price = extract_field(RE_VEST_PRICE, content, "Vest Price")
        raw_qty_released = extract_field(RE_QTY_RELEASED, content, "Qty Released")
        raw_qty_net = extract_field(RE_QTY_NET, content, "Qty Net")

        # Format Dates
        award_dt = datetime.strptime(raw_award_date, "%d-%b-%Y")
        release_dt = datetime.strptime(raw_release_date, "%d-%b-%Y")

        # Handle Stock Split Logic
        qty_rel_float = float(raw_qty_released)
        qty_net_float = float(raw_qty_net)

        if release_dt < SPLIT_DATE:
            qty_rel_float *= SPLIT_FACTOR
            qty_net_float *= SPLIT_FACTOR

        return StockData(
            award_date=award_dt.strftime("%Y/%m/%d"),
            award_id=award_id,
            release_date=release_dt.strftime("%Y/%m/%d"),
            vest_price=vest_price,
            quantity_released=f"{qty_rel_float:.3f}",
            quantity_net=f"{qty_net_float:.3f}",
        )

    except (PDFParsingError, ValueError) as e:
        logger.error(f"Skipping {pdf_path.name}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error processing {pdf_path.name}: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse stock reports and generate a CSV file."
    )
    parser.add_argument(
        "-i",
        "--in_folder",
        type=Path,
        default=Path("./reports/"),
        help="Folder containing source PDF reports.",
    )
    parser.add_argument(
        "-o",
        "--out_folder",
        type=Path,
        default=Path("output"),
        help="Destination folder for organized reports.",
    )
    parser.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="Organize (move/rename) reports into folders.",
    )
    parser.add_argument(
        "-w",
        "--write-csv",
        action="store_true",
        help="Write the parsed data to 'stocks.csv'.",
    )

    args = parser.parse_args()

    # Validation
    if not args.in_folder.exists():
        logger.error(f"Input folder '{args.in_folder}' does not exist.")
        return

    # Gather PDF files
    # rglob allows recursive search easily
    pdf_files = sorted(list(args.in_folder.rglob("*.pdf")))
    logger.info(f"Found {len(pdf_files)} PDF documents.")

    results: list[StockData] = []

    # Process Concurrently
    # PDF parsing is CPU-bound (text extraction) and IO-bound.
    # ProcessPoolExecutor avoids the GIL for CPU heavy regex/parsing.
    with ProcessPoolExecutor() as executor:
        future_to_file = {executor.submit(parse_pdf, p): p for p in pdf_files}

        for future in as_completed(future_to_file):
            data = future.result()
            if data:
                results.append(data)

                # If we need to move files, we do it here strictly after successful parsing
                if args.move:
                    # Note: We pass original paths. In a real threaded env,
                    # ensure file access doesn't conflict.
                    # Since we parsed it already, moving it now is safe.
                    original_path = future_to_file[future]
                    organize_report(
                        data.release_date, data.award_id, original_path, args.out_folder
                    )

    # Aggregation
    total_shares = sum(float(r.quantity_net) for r in results)
    logger.info(f"Successfully processed {len(results)} reports.")
    logger.info(f"Total GOOG Shares: {total_shares:.3f}")

    # Sort results by release_date (YYYY/MM/DD string format sorts chronologically)
    results.sort(key=lambda x: x.release_date)

    if args.write_csv and results:
        csv_path = Path("stocks.csv")
        try:
            with csv_path.open("w", newline="") as f:
                writer = csv.writer(f)
                # Header derived from NamedTuple fields
                writer.writerow(StockData._fields)
                writer.writerows(results)
            logger.info(f"CSV written to {csv_path.resolve()}")
        except OSError as e:
            logger.error(f"Failed to write CSV: {e}")


if __name__ == "__main__":
    main()
