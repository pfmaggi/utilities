# Stock Vesting Document Processor

This utility parses PDF files of Morgan Stanley stock vesting reports, extracts
key information, and organizes the reports by renaming them and moving them
into a structured folder hierarchy. It can also generate a CSV file with the
extracted data.

## Command-Line Arguments

The script accepts the following command-line arguments:

- `-i, --in_folder`: Specifies the folder where the stock vesting reports are located.
  - Default: `./reports/`
- `-o, --out_folder`: Specifies the folder where the processed reports will be organized.
  - Default: `output`
- `-m, --move`: When this flag is present, the script will move and rename the report files into a structured directory based on the release year.
- `-w, --write-csv`: When this flag is present, the script will write the extracted data to a CSV file named `stocks.csv` in the current directory.

## Examples

### Basic Usage (Dry Run)

By default, the script will run in a "dry run" mode, where it processes the files in the `reports` folder and prints the total number of shares processed without moving files or creating a CSV.

```bash
./stocks.py
```

### Process and Organize Reports

To process the reports from a specific folder, for example, `my_reports`, and organize them into an output folder named `processed_reports`, use the following command:

```bash
./stocks.py -i my_reports -o processed_reports -m
```

This command will:
1. Read the PDF reports from the `my_reports` folder.
2. Create a `processed_reports` folder if it doesn't exist.
3. For each report, create a subfolder within `processed_reports` corresponding to the release year.
4. Rename each report to the format `YYYYMMDD - Release Confirm - AWARD_ID.pdf`.
5. Move the renamed report into the corresponding year's subfolder.

### Generate a CSV Report

To process the reports and generate a `stocks.csv` file with the extracted data, use the `-w` flag:

```bash
./stocks.py -w
```

The `stocks.csv` file will contain the following columns:
- `award_date`
- `award_id`
- `release_date`
- `vest_price`
- `quantity_released`
- `quantity_net`

### Process, Organize, and Generate CSV

To perform all operations at once—process reports from a custom folder, organize them, and generate a CSV file—combine the flags:

```bash
./stocks.py -i my_reports -o processed_reports -m -w
```
