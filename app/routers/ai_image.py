"""AI Image generation and editing API endpoints."""

import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from app.config import settings
from app.services.ai_image_service import (
    generate_image,
    edit_image,
    get_style_presets,
    get_action_presets,
    check_api_key_configured,
    AIImageError
)
from app.middleware.usage_check import require_usage_limit


router = APIRouter(prefix="/api/ai-image", tags=["ai-image"])


class GenerateRequest(BaseModel):
    """Request model for image generation."""
    prompt: str
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"
    size: str = "1k"


@router.get("/check-api-key")
async def check_api_key():
    """Check if Google API key is configured."""
    return JSONResponse({
        "api_key_configured": check_api_key_configured()
    })


@router.get("/presets")
async def get_presets():
    """
    Get all available style and action presets.

    Returns:
        JSON with style_presets and action_presets
    """
    return JSONResponse({
        "style_presets": get_style_presets(),
        "action_presets": get_action_presets()
    })


@router.post("/generate")
@require_usage_limit(file_size_mb=0)
async def generate_ai_image(http_request: Request, request: GenerateRequest):
    """
    Generate an image from text prompt.

    Args:
        request: Generation parameters (prompt, style, aspect_ratio, size)

    Returns:
        Generated image file
    """
    if not check_api_key_configured():
        raise HTTPException(
            status_code=503,
            detail="Google API key not configured. Please set GOOGLE_API_KEY in .env file."
        )

    if not request.prompt or len(request.prompt.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Prompt must be at least 3 characters long"
        )

    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"generated_{unique_id}.png"
    output_path = settings.output_dir / output_filename

    try:
        # Generate image
        image_bytes, mime_type = generate_image(
            prompt=request.prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            size=request.size
        )

        # Save to file
        output_path.write_bytes(image_bytes)

        # Determine file extension from mime type
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp"
        }
        ext = ext_map.get(mime_type, ".png")

        # Return image file
        return FileResponse(
            path=output_path,
            media_type=mime_type,
            filename=f"generated{ext}",
            background=None
        )

    except AIImageError as e:
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/edit")
@require_usage_limit(file_size_mb=25)
async def edit_ai_image(
    request: Request,
    file: UploadFile = File(...),
    action: str = Form(...),
    custom_prompt: Optional[str] = Form(None),
    style: Optional[str] = Form(None)
):
    """
    Edit an existing image using AI.

    Args:
        file: Image file to edit
        action: Action preset name
        custom_prompt: Optional custom instructions
        style: Optional style for style-change action

    Returns:
        Edited image file
    """
    if not check_api_key_configured():
        raise HTTPException(
            status_code=503,
            detail="Google API key not configured. Please set GOOGLE_API_KEY in .env file."
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    unique_id = str(uuid.uuid4())[:8]
    input_filename = f"{unique_id}_input_{file.filename}"
    input_path = settings.upload_dir / input_filename

    output_filename = f"{unique_id}_edited.png"
    output_path = settings.output_dir / output_filename

    try:
        # Save uploaded file
        content = await file.read()
        input_path.write_bytes(content)

        # Edit image
        image_bytes, mime_type = edit_image(
            image_path=input_path,
            action=action,
            custom_prompt=custom_prompt,
            style=style
        )

        # Save edited image
        output_path.write_bytes(image_bytes)

        # Cleanup input
        input_path.unlink(missing_ok=True)

        # Determine file extension
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp"
        }
        ext = ext_map.get(mime_type, ".png")

        # Return edited image
        return FileResponse(
            path=output_path,
            media_type=mime_type,
            filename=f"edited{ext}",
            background=None
        )

    except AIImageError as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Edit failed: {str(e)}")
