#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "PyPDF2==3.*",
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

from PyPDF2 import PdfReader, PdfWriter
import argparse
from pathlib import Path
from typing import Optional


def process_args(
    front: Path,
    back: Path,
    output: Optional[Path] = None,
    overwrite: Optional[bool] = False,
) -> None:
    """
    Add all the pages alternating fronts and backs
    note: backs are in reverse order
    """
    print(f"Processing {front} and {back}")
    if not output:
        output = Path("merged_pdf")

    print(f"Output will be saved to: {output.resolve()}")

    # Validate input files exist
    for f in [front, back]:
        if not f.is_file():
            raise FileNotFoundError(f"Input file not found: {f.resolve()}")

    # Check output file exist
    if output.is_file() and not overwrite:
        raise FileExistsError(f"Output file already exist: {output.resolve()}")

    fronts = PdfReader(front)
    backs = PdfReader(back)

    if len(backs.pages) != len(fronts.pages):
        print(f"Pages {len(fronts.pages)} and {len(backs.pages)}")
        raise ValueError("The two input PDFs need to have the same number of pages")
    page_count = 2 * len(backs.pages)
    writer = PdfWriter()

    # Add all the pages alternating fronts and backs
    # note: backs are in reverse order
    for index, page in enumerate(fronts.pages):
        writer.add_page(page)
        writer.add_page(backs.pages[-1 - index])

    # save the new pdf to a file
    if output:
        with open(output.resolve(), "wb") as f:
            writer.write(f)
    else:
        with open("merged.pdf", "wb") as f:
            writer.write(f)

    print(f"Merged {page_count} pages")


def parse_arguments() -> argparse.Namespace:
    """Configure and parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Merge two PDF, the back pages are expected to be in "
        "reverse order: from last to first.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required positional arguments
    parser.add_argument("front", type=Path, help="PDF file with front pages")
    parser.add_argument(
        "back", type=Path, help="PDF file with back pages in reverse order"
    )

    # Optional output flag
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optional output filename for the merged PDF",
    )

    # Optional overwrite flag
    parser.add_argument(
        "-w", "--overwrite", action="store_true", help="Overwrite output file."
    )

    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_arguments()
        process_args(args.front, args.back, args.output, args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(f"Error: {e}")
        exit(1)
