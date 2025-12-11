"""PDF manipulation API endpoints."""

import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.services.pdf_service import (
    merge_pdfs,
    split_pdf_all,
    split_pdf_range,
    get_pdf_info,
    validate_pdf_file
)
from app.middleware.usage_check import require_usage_limit


router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.post("/info")
@require_usage_limit(file_size_mb=25)
async def get_pdf_information(request: Request, file: UploadFile = File(...)):
    """
    Get information about a PDF file.

    Args:
        file: PDF file to analyze

    Returns:
        JSON with page count and metadata
    """
    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate PDF
        if not validate_pdf_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        # Get info
        info = get_pdf_info(input_path)

        # Cleanup
        input_path.unlink(missing_ok=True)

        return JSONResponse(info)

    except HTTPException:
        raise
    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {str(e)}")


@router.post("/merge")
@require_usage_limit(file_size_mb=25)
async def merge_pdf_files(request: Request, files: List[UploadFile] = File(...)):
    """
    Merge multiple PDF files into one.

    Args:
        files: List of PDF files in merge order

    Returns:
        Merged PDF file
    """
    if not files or len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 PDF files required for merging"
        )

    unique_id = str(uuid.uuid4())[:8]
    input_paths = []

    try:
        # Save all uploaded files
        for file in files:
            input_filename = f"{unique_id}_{file.filename}"
            input_path = settings.upload_dir / input_filename

            content = await file.read()
            input_path.write_bytes(content)

            # Validate PDF
            if not validate_pdf_file(input_path):
                print(f"Skipping invalid PDF: {file.filename}")
                input_path.unlink(missing_ok=True)
                continue

            input_paths.append(input_path)

        if len(input_paths) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 valid PDF files required"
            )

        # Merge PDFs
        output_filename = f"merged_{unique_id}.pdf"
        output_path = settings.output_dir / output_filename

        merge_pdfs(input_paths, output_path)

        # Return merged file
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="merged.pdf",
            background=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
    finally:
        # Cleanup input files
        for path in input_paths:
            path.unlink(missing_ok=True)


@router.post("/split")
@require_usage_limit(file_size_mb=25)
async def split_pdf_file(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Form(...),
    pages: str = Form(None)
):
    """
    Split a PDF file.

    Args:
        file: PDF file to split
        mode: "all" to split all pages, "range" to extract specific pages
        pages: Page range for "range" mode (e.g., "1-5,10,15-20")

    Returns:
        ZIP file with extracted pages
    """
    if mode not in ["all", "range"]:
        raise HTTPException(
            status_code=400,
            detail="Mode must be 'all' or 'range'"
        )

    if mode == "range" and not pages:
        raise HTTPException(
            status_code=400,
            detail="Page range required for 'range' mode"
        )

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate PDF
        if not validate_pdf_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        # Split based on mode
        if mode == "all":
            output_path, page_count = split_pdf_all(input_path, settings.output_dir)
            download_filename = f"{Path(file.filename).stem}_split.zip"

        else:  # mode == "range"
            output_path, page_count = split_pdf_range(
                input_path,
                pages,
                settings.output_dir
            )

            # Determine filename and media type
            if output_path.suffix == '.zip':
                download_filename = f"{Path(file.filename).stem}_pages.zip"
            else:
                download_filename = output_path.name

        # Cleanup input
        input_path.unlink(missing_ok=True)

        # Determine media type
        media_type = "application/zip" if output_path.suffix == '.zip' else "application/pdf"

        # Return result
        return FileResponse(
            path=output_path,
            media_type=media_type,
            filename=download_filename,
            background=None
        )

    except HTTPException:
        raise
    except ValueError as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")
