#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "pypdf>=5.0.0",
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
import logging
import sys
from pathlib import Path

import pypdf

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def merge_pdfs(
    front_path: Path,
    back_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> None:
    """
    Interleave front and back PDF pages. Back pages are expected in reverse order.

    Uses a 'Happy Path' pattern with early exits for validation.
    """
    # Validation logic using Path methods
    if not front_path.is_file():
        raise FileNotFoundError(f"Front PDF missing: {front_path}")
    if not back_path.is_file():
        raise FileNotFoundError(f"Back PDF missing: {back_path}")

    # Check extensions
    if front_path.suffix.lower() != ".pdf":
        logger.warning(
            f"Front file '{front_path.name}' does not have a .pdf extension."
        )
    if back_path.suffix.lower() != ".pdf":
        logger.warning(f"Back file '{back_path.name}' does not have a .pdf extension.")

    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output exists (use --overwrite to bypass): {output_path}"
        )

    # Ensure output directory exists
    if not output_path.parent.exists():
        logger.info(f"Creating output directory: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Merging: {front_path.name} + {back_path.name}")

    try:
        reader_front = pypdf.PdfReader(front_path)
        reader_back = pypdf.PdfReader(back_path)
    except Exception as e:
        raise ValueError(f"Error reading PDF files: {e}")

    writer = pypdf.PdfWriter()

    front_pages = reader_front.pages
    back_pages = reader_back.pages

    # Use zip with reversed back_pages for cleaner iteration
    if (f_len := len(front_pages)) != (b_len := len(back_pages)):
        raise ValueError(f"Page mismatch: Front has {f_len} pages, Back has {b_len}.")

    # Interleave pages
    for f_page, b_page in zip(front_pages, reversed(back_pages)):
        writer.add_page(f_page)
        writer.add_page(b_page)

    # Use context manager for safe file writing
    with output_path.open("wb") as f:
        writer.write(f)

    logger.info(
        f"Successfully merged {len(writer.pages)} total pages to {output_path.name}"
    )


def parse_arguments(args: list[str]) -> argparse.Namespace:
    """Configures CLI with modern defaults."""
    parser = argparse.ArgumentParser(
        description="Merge interleaved PDF scans (fronts + reversed backs).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("front", type=Path, help="PDF with front pages")
    parser.add_argument("back", type=Path, help="PDF with back pages (reverse order)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("merged_output.pdf"),
        help="Output file path",
    )
    parser.add_argument(
        "-w", "--overwrite", action="store_true", help="Overwrite existing file"
    )

    return parser.parse_args(args)


def main() -> None:
    """Main entry point with structured error handling."""
    try:
        ns = parse_arguments(sys.argv[1:])
        merge_pdfs(ns.front, ns.back, ns.output, overwrite=ns.overwrite)
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.error("\nAborted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
