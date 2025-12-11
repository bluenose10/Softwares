"""Audio extraction API endpoints."""

import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.services.audio_service import (
    extract_audio,
    get_video_info,
    get_supported_formats,
    validate_video_file,
    check_ffmpeg_installed,
    check_ffprobe_installed
)
from app.middleware.usage_check import require_usage_limit


router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/formats")
async def list_supported_formats():
    """Get list of supported video inputs and audio outputs."""
    return get_supported_formats()


@router.get("/check-ffmpeg")
async def check_ffmpeg_availability():
    """Check if FFmpeg and FFprobe are installed."""
    return JSONResponse({
        "ffmpeg_installed": check_ffmpeg_installed(),
        "ffprobe_installed": check_ffprobe_installed()
    })


@router.post("/info")
@require_usage_limit(file_size_mb=25)
async def get_video_information(request: Request, file: UploadFile = File(...)):
    """
    Get information about a video file.

    Args:
        file: Video file to analyze

    Returns:
        JSON with duration, size, codecs
    """
    if not check_ffprobe_installed():
        raise HTTPException(
            status_code=503,
            detail="FFprobe is not installed. Please install FFmpeg to use this feature."
        )

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate video
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Get info
        info = get_video_info(input_path)

        # Check if video has audio
        if not info.get("has_audio", False):
            input_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="Video does not contain an audio stream"
            )

        # Cleanup
        input_path.unlink(missing_ok=True)

        return JSONResponse(info)

    except HTTPException:
        raise
    except RuntimeError as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to read video: {str(e)}")


@router.post("/extract")
@require_usage_limit(file_size_mb=25)
async def extract_audio_from_video(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form(...),
    bitrate: int = Form(192)
):
    """
    Extract audio from a video file.

    Args:
        file: Video file
        format: Target audio format (mp3, aac, wav, flac, ogg)
        bitrate: Bitrate in kbps (for lossy formats)

    Returns:
        Audio file
    """
    if not check_ffmpeg_installed():
        raise HTTPException(
            status_code=503,
            detail="FFmpeg is not installed. Please install FFmpeg to use this feature."
        )

    # Validate format
    supported = get_supported_formats()
    format = format.lower()

    if format not in supported["audio_outputs"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: {', '.join(supported['audio_outputs'])}"
        )

    # Validate bitrate
    if bitrate not in supported["bitrate_options"]:
        bitrate = 192  # Default

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_{file.filename}"
    input_path = settings.upload_dir / input_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Validate video
        if not validate_video_file(input_path):
            input_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Extract audio
        output_path = extract_audio(
            input_path,
            format,
            bitrate,
            settings.output_dir
        )

        # Cleanup input
        input_path.unlink(missing_ok=True)

        # Return audio file
        return FileResponse(
            path=output_path,
            media_type=f"audio/{format}",
            filename=f"{Path(file.filename).stem}.{format}",
            background=None
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
