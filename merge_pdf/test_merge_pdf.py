import unittest
import shutil
import tempfile
from pathlib import Path
import logging
from pypdf import PdfWriter, PdfReader

# Import the function to be tested
from merge_pdf import merge_pdfs


class TestMergePDF(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.front_path = Path(self.test_dir) / "front.pdf"
        self.back_path = Path(self.test_dir) / "back.pdf"
        self.output_path = Path(self.test_dir) / "output.pdf"

        # Suppress logging during tests
        logging.getLogger("merge_pdf").setLevel(logging.CRITICAL)

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def create_pdf(self, path: Path, pages: int):
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=100, height=100)
        with open(path, "wb") as f:
            writer.write(f)

    def test_merge_success(self):
        self.create_pdf(self.front_path, 3)
        self.create_pdf(self.back_path, 3)

        merge_pdfs(self.front_path, self.back_path, self.output_path)

        self.assertTrue(self.output_path.exists())
        reader = PdfReader(self.output_path)
        self.assertEqual(len(reader.pages), 6)

    def test_page_mismatch(self):
        self.create_pdf(self.front_path, 3)
        self.create_pdf(self.back_path, 2)

        with self.assertRaisesRegex(ValueError, "Page mismatch"):
            merge_pdfs(self.front_path, self.back_path, self.output_path)

    def test_file_not_found_front(self):
        self.create_pdf(self.back_path, 1)
        with self.assertRaisesRegex(FileNotFoundError, "Front PDF missing"):
            merge_pdfs(self.front_path, self.back_path, self.output_path)

    def test_file_not_found_back(self):
        self.create_pdf(self.front_path, 1)
        with self.assertRaisesRegex(FileNotFoundError, "Back PDF missing"):
            merge_pdfs(self.front_path, self.back_path, self.output_path)

    def test_output_exists_no_overwrite(self):
        self.create_pdf(self.front_path, 1)
        self.create_pdf(self.back_path, 1)
        self.output_path.touch()

        with self.assertRaisesRegex(FileExistsError, "Output exists"):
            merge_pdfs(self.front_path, self.back_path, self.output_path)

    def test_output_exists_overwrite(self):
        self.create_pdf(self.front_path, 1)
        self.create_pdf(self.back_path, 1)
        self.output_path.touch()

        merge_pdfs(self.front_path, self.back_path, self.output_path, overwrite=True)

        reader = PdfReader(self.output_path)
        self.assertEqual(len(reader.pages), 2)

    def test_create_output_dir(self):
        self.create_pdf(self.front_path, 1)
        self.create_pdf(self.back_path, 1)
        nested_output = Path(self.test_dir) / "subdir" / "output.pdf"

        merge_pdfs(self.front_path, self.back_path, nested_output)

        self.assertTrue(nested_output.exists())

    def test_invalid_pdf_content(self):
        # Create dummy text files named .pdf
        with open(self.front_path, "w") as f:
            f.write("Not a PDF")
        with open(self.back_path, "w") as f:
            f.write("Not a PDF")

        with self.assertRaisesRegex(ValueError, "Error reading PDF files"):
            merge_pdfs(self.front_path, self.back_path, self.output_path)


if __name__ == "__main__":
    unittest.main()
