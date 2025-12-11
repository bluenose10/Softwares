"""PDF manipulation service using pypdf."""

import re
import zipfile
from pathlib import Path
from typing import List, Tuple, Dict
from pypdf import PdfReader, PdfWriter


def get_pdf_info(pdf_path: Path) -> Dict:
    """
    Get information about a PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with page count and other metadata
    """
    try:
        reader = PdfReader(pdf_path)
        return {
            "page_count": len(reader.pages),
            "filename": pdf_path.name,
            "size": pdf_path.stat().st_size
        }
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {str(e)}")


def merge_pdfs(pdf_paths: List[Path], output_path: Path) -> Path:
    """
    Merge multiple PDF files into one.

    Args:
        pdf_paths: List of PDF file paths in merge order
        output_path: Path for the merged PDF

    Returns:
        Path to merged PDF

    Raises:
        ValueError: If no PDFs provided or merge fails
    """
    if not pdf_paths:
        raise ValueError("No PDF files provided for merging")

    try:
        writer = PdfWriter()

        # Add all pages from all PDFs in order
        for pdf_path in pdf_paths:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)

        # Write merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    except Exception as e:
        raise ValueError(f"Failed to merge PDFs: {str(e)}")


def split_pdf_all(pdf_path: Path, output_dir: Path) -> Tuple[Path, int]:
    """
    Split a PDF into individual pages.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save individual pages

    Returns:
        Tuple of (ZIP path, number of pages)

    Raises:
        ValueError: If split fails
    """
    try:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)

        if page_count == 0:
            raise ValueError("PDF has no pages")

        # Create individual PDFs for each page
        page_paths = []
        base_name = pdf_path.stem

        for page_num in range(page_count):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])

            # Page numbers are 1-indexed for user display
            page_path = output_dir / f"{base_name}_page_{page_num + 1}.pdf"
            with open(page_path, 'wb') as output_file:
                writer.write(output_file)

            page_paths.append(page_path)

        # Create ZIP archive
        zip_path = output_dir / f"{base_name}_split.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for page_path in page_paths:
                zipf.write(page_path, page_path.name)

        # Clean up individual PDFs (keep only ZIP)
        for page_path in page_paths:
            page_path.unlink()

        return zip_path, page_count

    except Exception as e:
        raise ValueError(f"Failed to split PDF: {str(e)}")


def parse_page_range(range_string: str, max_pages: int) -> List[int]:
    """
    Parse page range string into list of page numbers.

    Supports formats:
    - "1,3,5" -> [1, 3, 5]
    - "1-5" -> [1, 2, 3, 4, 5]
    - "1-3,5,7-9" -> [1, 2, 3, 5, 7, 8, 9]

    Args:
        range_string: Page range specification
        max_pages: Maximum valid page number

    Returns:
        Sorted list of unique page numbers (1-indexed)

    Raises:
        ValueError: If range format is invalid or pages out of bounds
    """
    if not range_string or not range_string.strip():
        raise ValueError("Page range cannot be empty")

    pages = set()

    # Split by comma
    parts = range_string.split(',')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if it's a range (e.g., "1-5")
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())

                if start < 1 or end > max_pages:
                    raise ValueError(f"Page range {start}-{end} is out of bounds (1-{max_pages})")

                if start > end:
                    raise ValueError(f"Invalid range: {start}-{end} (start > end)")

                pages.update(range(start, end + 1))

            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid range format: {part}")
                raise

        else:
            # Single page number
            try:
                page_num = int(part.strip())

                if page_num < 1 or page_num > max_pages:
                    raise ValueError(f"Page {page_num} is out of bounds (1-{max_pages})")

                pages.add(page_num)

            except ValueError:
                raise ValueError(f"Invalid page number: {part}")

    if not pages:
        raise ValueError("No valid pages specified")

    return sorted(list(pages))


def split_pdf_range(
    pdf_path: Path,
    page_range: str,
    output_dir: Path
) -> Tuple[Path, int]:
    """
    Extract specific pages from a PDF.

    Args:
        pdf_path: Path to PDF file
        page_range: Page range string (e.g., "1-5,10,15-20")
        output_dir: Directory to save output

    Returns:
        Tuple of (output path, number of pages extracted)
        - If single page: returns PDF path
        - If multiple pages: returns ZIP path

    Raises:
        ValueError: If extraction fails
    """
    try:
        reader = PdfReader(pdf_path)
        max_pages = len(reader.pages)

        # Parse page range
        page_numbers = parse_page_range(page_range, max_pages)

        if not page_numbers:
            raise ValueError("No valid pages to extract")

        base_name = pdf_path.stem

        # If only one page, return as single PDF
        if len(page_numbers) == 1:
            writer = PdfWriter()
            # Page numbers are 1-indexed, but array is 0-indexed
            writer.add_page(reader.pages[page_numbers[0] - 1])

            output_path = output_dir / f"{base_name}_page_{page_numbers[0]}.pdf"
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            return output_path, 1

        # Multiple pages: create individual PDFs and ZIP them
        page_paths = []

        for page_num in page_numbers:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num - 1])  # Convert to 0-indexed

            page_path = output_dir / f"{base_name}_page_{page_num}.pdf"
            with open(page_path, 'wb') as output_file:
                writer.write(output_file)

            page_paths.append(page_path)

        # Create ZIP archive
        zip_path = output_dir / f"{base_name}_pages.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for page_path in page_paths:
                zipf.write(page_path, page_path.name)

        # Clean up individual PDFs
        for page_path in page_paths:
            page_path.unlink()

        return zip_path, len(page_numbers)

    except Exception as e:
        raise ValueError(f"Failed to extract pages: {str(e)}")


def validate_pdf_file(file_path: Path) -> bool:
    """
    Validate if a file is a valid PDF.

    Args:
        file_path: Path to file

    Returns:
        True if file is a valid PDF
    """
    try:
        reader = PdfReader(file_path)
        # Check if it has at least one page
        return len(reader.pages) > 0
    except Exception:
        return False
