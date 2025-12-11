"""Video processing API endpoints."""

import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Body, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from app.config import settings
from app.services.video_service import (
    split_video,
    get_video_info,
    get_video_duration,
    calculate_split_times,
    format_duration,
    create_video_zip,
    validate_video_file,
    check_ffmpeg_installed,
    compress_target_size,
    compress_quality,
    compress_resolution,
    estimate_output_size
)
from app.middleware.usage_check import require_usage_limit


router = APIRouter(prefix="/api/video", tags=["video"])


class LocalVideoRequest(BaseModel):
    """Request model for local video operations."""
    path: str
    parts: Optional[int] = None
    output_dir: Optional[str] = None


@router.get("/check-ffmpeg")
async def check_ffmpeg_availability():
    """Check if FFmpeg is installed."""
    return JSONResponse({
        "ffmpeg_installed": check_ffmpeg_installed()
    })


@router.post("/info")
@require_usage_limit(file_size_mb=25)
async def get_video_information(request: Request, file: UploadFile = File(...)):
    """
    Get information about an uploaded video file.

    Args:
        file: Video file to analyze

    Returns:
        JSON with duration, size, codecs
    """
    if not check_ffmpeg_installed():
        raise HTTPException(
            status_code=503,
            detail="FFmpeg is not installed"
        )

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Get info
        info = get_video_info(input_path)

        # Cleanup
        input_path.unlink(missing_ok=True)

        return JSONResponse(info)

    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/info-local")
@require_usage_limit(file_size_mb=25)
async def get_local_video_info(request: Request, local_request: LocalVideoRequest = Body(...)):
    """
    Get information about a video file from local path.

    Args:
        request: Contains local file path

    Returns:
        JSON with video metadata
    """
    if not check_ffmpeg_installed():
        raise HTTPException(
            status_code=503,
            detail="FFmpeg is not installed"
        )

    try:
        video_path = Path(request.path)

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not validate_video_file(video_path):
            raise HTTPException(status_code=400, detail="Invalid video file")

        info = get_video_info(video_path)
        return JSONResponse(info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/split-preview")
@require_usage_limit(file_size_mb=25)
async def preview_split_times(
    request: Request,
    file: Optional[UploadFile] = File(None),
    parts: int = Form(...)
):
    """
    Preview split times without actually splitting.

    Args:
        file: Optional video file (or will use cached duration)
        parts: Number of parts

    Returns:
        JSON with split time previews
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    if parts < 2 or parts > 20:
        raise HTTPException(status_code=400, detail="Parts must be between 2 and 20")

    unique_id = str(uuid.uuid4())[:8]
    input_path = None

    try:
        if file:
            input_filename = f"{unique_id}_{file.filename}"
            input_path = settings.upload_dir / input_filename

            content = await file.read()
            input_path.write_bytes(content)

            duration = get_video_duration(input_path)
        else:
            raise HTTPException(status_code=400, detail="No video file provided")

        split_times = calculate_split_times(duration, parts)

        preview = []
        for i, (start, end) in enumerate(split_times, 1):
            preview.append({
                "part": i,
                "start": start,
                "end": end,
                "start_formatted": format_duration(start),
                "end_formatted": format_duration(end),
                "duration": end - start,
                "duration_formatted": format_duration(end - start)
            })

        return JSONResponse({
            "total_duration": duration,
            "total_duration_formatted": format_duration(duration),
            "num_parts": parts,
            "parts": preview
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            input_path.unlink(missing_ok=True)


@router.post("/split")
@require_usage_limit(file_size_mb=25)
async def split_uploaded_video(
    request: Request,
    file: UploadFile = File(...),
    parts: int = Form(...)
):
    """
    Split an uploaded video into multiple parts.

    Args:
        file: Video file to split
        parts: Number of parts (2-20)

    Returns:
        ZIP file with all video parts
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    if parts < 2 or parts > 20:
        raise HTTPException(status_code=400, detail="Parts must be between 2 and 20")

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Split video
        output_paths = split_video(input_path, parts, settings.output_dir)

        # Create ZIP
        zip_filename = f"{Path(file.filename).stem}_split.zip"
        zip_path = settings.output_dir / zip_filename
        create_video_zip(output_paths, zip_path)

        # Cleanup input and individual parts
        input_path.unlink(missing_ok=True)
        for path in output_paths:
            path.unlink(missing_ok=True)

        # Return ZIP
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=zip_filename,
            background=None
        )

    except HTTPException:
        raise
    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")


@router.post("/split-local")
@require_usage_limit(file_size_mb=25)
async def split_local_video(request: Request, local_request: LocalVideoRequest = Body(...)):
    """
    Split a video from local file path.

    Args:
        request: Contains path, parts, and optional output_dir

    Returns:
        JSON with paths to split video files
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    if not local_request.parts or local_request.parts < 2 or local_request.parts > 20:
        raise HTTPException(status_code=400, detail="Parts must be between 2 and 20")

    try:
        video_path = Path(local_request.path)

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not validate_video_file(video_path):
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Determine output directory
        if local_request.output_dir:
            output_dir = Path(local_request.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = settings.output_dir

        # Split video
        output_paths = split_video(video_path, local_request.parts, output_dir)

        return JSONResponse({
            "status": "success",
            "num_parts": len(output_paths),
            "output_files": [str(p) for p in output_paths]
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")


# ============================================================================
# VIDEO COMPRESSION ENDPOINTS
# ============================================================================

@router.post("/compress/target-size")
@require_usage_limit(file_size_mb=25)
async def compress_video_target_size(
    request: Request,
    file: UploadFile = File(...),
    target_size_mb: float = Form(...)
):
    """
    Compress video to target file size using two-pass encoding.

    Args:
        file: Video file to compress
        target_size_mb: Target output size in MB

    Returns:
        Compressed video file
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    if target_size_mb <= 0:
        raise HTTPException(status_code=400, detail="Target size must be positive")

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    output_filename = f"{unique_id}_compressed_{file.filename}"
    output_path = settings.output_dir / output_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Compress
        compress_target_size(input_path, target_size_mb, output_path)

        # Cleanup input
        input_path.unlink(missing_ok=True)

        # Return compressed video
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"compressed_{file.filename}",
            background=None
        )

    except ValueError as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")


@router.post("/compress/quality")
@require_usage_limit(file_size_mb=25)
async def compress_video_quality(
    request: Request,
    file: UploadFile = File(...),
    preset: str = Form(...)
):
    """
    Compress video using quality preset (CRF encoding).

    Args:
        file: Video file to compress
        preset: Quality preset (low/medium/high)

    Returns:
        Compressed video file
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    if preset.lower() not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Invalid preset. Use low/medium/high")

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    output_filename = f"{unique_id}_compressed_{file.filename}"
    output_path = settings.output_dir / output_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Compress
        compress_quality(input_path, preset, output_path)

        # Cleanup input
        input_path.unlink(missing_ok=True)

        # Return compressed video
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"compressed_{file.filename}",
            background=None
        )

    except ValueError as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")


@router.post("/compress/resolution")
@require_usage_limit(file_size_mb=25)
async def compress_video_resolution(
    request: Request,
    file: UploadFile = File(...),
    resolution: str = Form(...),
    preset: str = Form(...)
):
    """
    Compress video by downscaling to target resolution.

    Args:
        file: Video file to compress
        resolution: Target resolution (2160p/1440p/1080p/720p/480p/360p)
        preset: Quality preset (low/medium/high)

    Returns:
        Compressed video file
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    valid_resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p"]
    if resolution not in valid_resolutions:
        raise HTTPException(status_code=400, detail=f"Invalid resolution. Use: {', '.join(valid_resolutions)}")

    if preset.lower() not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Invalid preset. Use low/medium/high")

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    output_filename = f"{unique_id}_compressed_{file.filename}"
    output_path = settings.output_dir / output_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Compress
        compress_resolution(input_path, resolution, preset, output_path)

        # Cleanup input
        input_path.unlink(missing_ok=True)

        # Return compressed video
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"compressed_{file.filename}",
            background=None
        )

    except ValueError as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")


@router.post("/compress/estimate")
@require_usage_limit(file_size_mb=25)
async def estimate_compression(
    request: Request,
    file: Optional[UploadFile] = File(None),
    mode: str = Form(...),
    target_size_mb: Optional[float] = Form(None),
    preset: Optional[str] = Form(None),
    resolution: Optional[str] = Form(None)
):
    """
    Estimate output size without actually compressing.

    Args:
        file: Video file to analyze
        mode: Compression mode (target_size/quality/resolution)
        target_size_mb: Target size for target_size mode
        preset: Quality preset for quality/resolution mode
        resolution: Target resolution for resolution mode

    Returns:
        JSON with estimated size and reduction percentage
    """
    if not check_ffmpeg_installed():
        raise HTTPException(status_code=503, detail="FFmpeg is not installed")

    if mode not in ["target_size", "quality", "resolution"]:
        raise HTTPException(status_code=400, detail="Invalid mode")

    if not file:
        raise HTTPException(status_code=400, detail="No video file provided")

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Estimate
        estimate = estimate_output_size(
            input_path,
            mode,
            target_size_mb,
            preset,
            resolution
        )

        # Cleanup
        input_path.unlink(missing_ok=True)

        return JSONResponse(estimate)

    except HTTPException:
        input_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Estimation failed: {str(e)}")
