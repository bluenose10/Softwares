"""Image conversion API endpoints."""

import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.services.image_service import (
    convert_image,
    get_supported_formats,
    validate_image_file,
    convert_multiple_images,
    create_zip_archive
)
from app.middleware.usage_check import require_usage_limit


router = APIRouter(prefix="/api/image", tags=["image"])


@router.get("/formats")
async def list_supported_formats():
    """Get list of supported input and output formats."""
    return get_supported_formats()


@router.post("/convert")
@require_usage_limit(file_size_mb=25)  # Enforce free tier limits
async def convert_single_image(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form(...),
    quality: int = Form(85)
):
    """
    Convert a single image to the specified format.

    Args:
        file: Image file to convert
        format: Target format (png, jpg, webp, etc.)
        quality: Quality for lossy formats (1-100)

    Returns:
        Converted image file
    """
    # Validate format
    supported = get_supported_formats()
    format = format.lower().replace("jpeg", "jpg")

    if format not in supported["output"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: {', '.join(supported['output'])}"
        )

    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate image
        if not validate_image_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid or unsupported image file"
            )

        # Convert image
        output_path = convert_image(input_path, format, quality)

        # Return converted file
        return FileResponse(
            path=output_path,
            media_type=f"image/{format}",
            filename=f"{Path(file.filename).stem}.{format}",
            background=None  # Will handle cleanup after response
        )

    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/convert-bulk")
async def convert_multiple_images_endpoint(
    files: List[UploadFile] = File(...),
    format: str = Form(...),
    quality: int = Form(85)
):
    """
    Convert multiple images to the specified format and return as ZIP.

    Args:
        files: List of image files to convert
        format: Target format (png, jpg, webp, etc.)
        quality: Quality for lossy formats (1-100)

    Returns:
        ZIP file containing all converted images
    """
    # Validate format
    supported = get_supported_formats()
    format = format.lower().replace("jpeg", "jpg")

    if format not in supported["output"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: {', '.join(supported['output'])}"
        )

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    unique_id = str(uuid.uuid4())[:8]
    input_paths = []
    output_paths = []

    try:
        # Save all uploaded files
        for file in files:
            input_filename = f"{unique_id}_{file.filename}"
            input_path = settings.upload_dir / input_filename

            content = await file.read()
            input_path.write_bytes(content)

            # Validate image
            if not validate_image_file(input_path):
                print(f"Skipping invalid image: {file.filename}")
                input_path.unlink(missing_ok=True)
                continue

            input_paths.append(input_path)

        if not input_paths:
            raise HTTPException(status_code=400, detail="No valid images provided")

        # Convert all images
        results = convert_multiple_images(input_paths, format, quality)

        if not results:
            raise HTTPException(status_code=500, detail="Failed to convert any images")

        # Collect output paths
        output_paths = [output_path for _, output_path in results]

        # Create ZIP archive
        zip_filename = f"converted_images_{unique_id}.zip"
        zip_path = settings.output_dir / zip_filename
        create_zip_archive(output_paths, zip_path)

        # Return ZIP file
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename="converted_images.zip",
            background=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk conversion failed: {str(e)}")
    finally:
        # Cleanup will be handled by FastAPI's background tasks in production
        # For now, files remain until manual cleanup
        pass


@router.delete("/cleanup")
async def cleanup_temp_files():
    """
    Clean up temporary files in upload and output directories.
    This is a manual cleanup endpoint.
    """
    try:
        upload_files = list(settings.upload_dir.glob("*"))
        output_files = list(settings.output_dir.glob("*"))

        # Remove all files except .gitkeep
        deleted_count = 0
        for file_path in upload_files + output_files:
            if file_path.name != ".gitkeep" and file_path.is_file():
                file_path.unlink()
                deleted_count += 1

        return JSONResponse({
            "status": "success",
            "deleted_files": deleted_count
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
