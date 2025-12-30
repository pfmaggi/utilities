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

from datetime import datetime

import PyPDF2
import csv
import os
import re
import argparse


def organize_report(
    release_date: str, award_id: str, old_filepath: str, output_path: str
):
    """
    Organize the report into a folder with the year of the release date.

    :param release_date: str - Release date in format YYYY/MM/DD
    :param award_id: str - Award ID
    :param old_filepath: str - Full path to the original report file
    :param output_path: str - Path to the output folder
    """
    release_date_dt = datetime.strptime(release_date, "%Y/%m/%d")
    year = str(release_date_dt.year)
    year_folder = os.path.join(output_path, year)

    if not os.path.exists(year_folder):
        os.makedirs(year_folder)

    # Define the new filename format.
    new_filename = (
        f"{release_date_dt.strftime('%Y%m%d')} - Release Confirm - {award_id}.pdf"
    )

    new_filepath = os.path.join(year_folder, new_filename)

    os.rename(old_filepath, new_filepath)


def parse(pdf_file_path: str) -> dict[str, str]:
    """
    Parse the given file and return a dictionary with the relevant details

    :param pdf_file_path: str - full path to a pdf report
    :return: Dict[str, str] - Dictionary of data extracted from PDF
    """
    reader = PyPDF2.PdfReader(open(pdf_file_path, "rb"))
    page = reader.pages[0]
    content = page.extract_text()

    award_date = ""
    award_id = ""
    release_date = ""
    vest_price = ""
    quantity_released = ""
    quantity_net = ""

    try:
        award_date = re.findall(r".*Award.?Date: (\d{2}-\w{3}-\d{4})", content)[0]
        award_id = re.findall(r".*Award.?ID: (C\d{6,7})", content)[0]
        release_date = re.findall(r".*Release.?Date: (\d{2}-\w{3}-\d{4})", content)[0]
        vest_price = re.findall(r".*FMV.?@.?Vest: (\$\d?,?\d{2,3}.\d{4})", content)[0]
        quantity_released = re.findall(
            r".*Quantity.?Released: (\d{1,3}\.\d{4}\s?)", content
        )[0].strip()
        quantity_net = re.findall(r".*Net.?Quantity: (\d{1,3}\.\d{4}\s?)", content)[
            0
        ].strip()
    except IndexError:
        # Handle cases where data extraction fails.
        print(
            f"There's an issue in the file: {pdf_file_path} with the content:\n{content}"
        )
        print(f"award_date={award_date}")
        print(f"award_id={award_id}")
        print(f"release_date={release_date}")
        print(f"vest_price={vest_price}")
        print(f"quantity_released={quantity_released}")
        print(f"quantity_net={quantity_net}")
        exit(1)

    # Reformat date strings to a standard format.
    award_date_reformatted = datetime.strptime(award_date, "%d-%b-%Y").strftime(
        "%Y/%m/%d"
    )
    release_date_dt = datetime.strptime(release_date, "%d-%b-%Y")
    release_date_reformatted = release_date_dt.strftime("%Y/%m/%d")

    # Define the split date for the stock split.
    split_date = datetime(2022, 7, 15)

    # Adjust quantity for stock split before split_date
    if release_date_dt < split_date:
        quantity_released = f"{float(quantity_released) * 20:.3f}"
        quantity_net = f"{float(quantity_net) * 20:.3f}"

    return dict(
        award_date=award_date_reformatted,
        award_id=award_id,
        release_date=release_date_reformatted,
        vest_price=vest_price,
        quantity_released=quantity_released,
        quantity_net=quantity_net,
    )


def get_reports_filenames(path: str) -> list[str]:
    """
    Return a list of filenames included in the path folder and its subfolders.

    :param path: str - folder path
    :return: List[str] - List of full pathnames.
    """
    file_paths: list[str] = []
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            file_paths.append(os.path.join(dirpath, filename))
    return sorted(file_paths)


if __name__ == "__main__":
    # Set up an argument parser to handle command-line inputs.
    parser = argparse.ArgumentParser(
        description="Parse stock reports and generate a CSV file."
    )
    parser.add_argument(
        "-i",
        "--in_folder",
        type=str,
        default="./reports/",
        help="Folder where the reports are located.",
    )
    parser.add_argument(
        "-o",
        "--out_folder",
        type=str,
        default="output",
        help="Folder where the reports will be organized.",
    )
    parser.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="Organize the reports into folders.",
    )
    parser.add_argument(
        "-w",
        "--write-csv",
        action="store_true",
        help="Write the output to a CSV file.",
    )
    args = parser.parse_args()

    # Set input and output paths from command-line arguments.
    INPUT_PATH = args.in_folder
    OUTPUT_PATH = args.out_folder

    # Get the list of report filenames.
    filepaths = get_reports_filenames(INPUT_PATH)

    print(f"Release Docs: {len(filepaths)}")
    quantity_sum: float = 0.0
    rows = []

    # Process each report file.
    for filepath in filepaths:
        # Skip non-PDF files.
        if not filepath.lower().endswith(".pdf"):
            print(f"{filepath} not evaluated")
            continue

        # Parse the report to extract data.
        data = parse(filepath)
        rows.append(data)

        # Sum the net quantity of shares.
        quantity_sum += float(data.get("quantity_net", 0))

        # Organize the report if the '--organize' flag is set.
        if args.move:
            organize_report(
                data["release_date"], data["award_id"], filepath, OUTPUT_PATH
            )

    print(f"Processed {quantity_sum:.3f} GOOG Shares")

    # Write the extracted data to a CSV file if the '--write-csv' flag is set.
    if args.write_csv:
        with open("stocks.csv", "w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=data.keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
