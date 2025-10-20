# Merge PDF

I have a automatic feed scanner that only handle single sided paper.
This little utility allows to combine two files that contains, one the
front pages and one the back pages in reverse order (that's how I scan
my documents).

## Arguments

The script accepts the following arguments:

- `front`: (Required) The path to the PDF file with the front pages.
- `back`: (Required) The path to the PDF file with the back pages, in reverse order.
- `-o`, `--output`: (Optional) The desired output filename for the merged PDF.
- `-w`, `--overwrite`: (Optional) A flag to allow overwriting the output file if it already exists.

## Usage Examples

Merge `front.pdf` and `back.pdf` into a new file named `merged.pdf`:

```bash
./merge_pdf.py front.pdf back.pdf -o merged.pdf
```

Merge `mydocs/front_pages.pdf` and `mydocs/back_pages.pdf` and overwrite the output file if it exists:

```bash
./merge_pdf.py mydocs/front_pages.pdf mydocs/back_pages.pdf -o merged.pdf -w
```
