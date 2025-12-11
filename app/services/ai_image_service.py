"""AI Image generation and editing service using Google Gemini."""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()


class AIImageError(Exception):
    """Custom exception for AI image processing errors."""
    pass


# Style presets for image generation
STYLE_PRESETS = {
    "photorealistic": "photorealistic, highly detailed, professional photography, sharp focus, natural lighting",
    "digital_art": "digital art, vibrant colors, detailed illustration, professional artwork",
    "watercolor": "watercolor painting style, soft edges, artistic brush strokes, delicate colors",
    "minimalist": "minimalist design, clean lines, simple composition, modern aesthetic",
    "3d_render": "3D rendered, CGI, highly detailed, realistic lighting, professional render",
    "anime": "anime style, manga illustration, Japanese animation aesthetic, vibrant colors"
}

# Action presets for image editing
ACTION_PRESETS = {
    "remove_background": "Remove the background from this image and make it transparent. Keep the main subject intact.",
    "change_style": "Transform this image into a {style} artistic style while preserving the main elements and composition.",
    "add_elements": "Add the following to this image naturally and seamlessly: {prompt}",
    "remove_object": "Remove {prompt} from this image and fill the area naturally to maintain coherence.",
    "enhance_quality": "Enhance this image by improving clarity, sharpness, and detail. Make it look more professional.",
    "color_correction": "Correct and enhance the colors in this image. Improve white balance, saturation, and overall color harmony."
}

# Aspect ratio mappings
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "4:5": (1024, 1280),
    "9:16": (1024, 1820),
    "16:9": (1820, 1024)
}

# Size multipliers
SIZE_MULTIPLIERS = {
    "1k": 1.0,
    "2k": 2.0,
    "4k": 4.0
}


def _get_gemini_client() -> genai.Client:
    """
    Get Gemini API client.

    Returns:
        Initialized Gemini client

    Raises:
        AIImageError: If API key is not configured
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise AIImageError(
            "Google API key not configured. Please set GOOGLE_API_KEY in .env file."
        )

    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        raise AIImageError(f"Failed to initialize Gemini client: {str(e)}")


def get_style_presets() -> Dict[str, str]:
    """
    Get all available style presets.

    Returns:
        Dictionary mapping style names to descriptions
    """
    return {
        "photorealistic": "Photorealistic",
        "digital_art": "Digital Art",
        "watercolor": "Watercolor",
        "minimalist": "Minimalist",
        "3d_render": "3D Render",
        "anime": "Anime/Manga"
    }


def get_action_presets() -> Dict[str, str]:
    """
    Get all available edit action presets.

    Returns:
        Dictionary mapping action names to descriptions
    """
    return {
        "remove_background": "Remove Background",
        "change_style": "Change Style",
        "add_elements": "Add Elements",
        "remove_object": "Remove Object",
        "enhance_quality": "Enhance Quality",
        "color_correction": "Color Correction"
    }


def _build_generation_prompt(user_prompt: str, style: str) -> str:
    """
    Build full generation prompt with style modifiers.

    Args:
        user_prompt: User's description of the image
        style: Style preset name

    Returns:
        Complete prompt with style modifiers
    """
    style_modifier = STYLE_PRESETS.get(style, "")

    if style_modifier:
        return f"{user_prompt}. Style: {style_modifier}"
    else:
        return user_prompt


def _build_edit_prompt(action: str, custom_prompt: Optional[str] = None, style: Optional[str] = None) -> str:
    """
    Build edit instruction prompt.

    Args:
        action: Action preset name
        custom_prompt: Custom user instructions
        style: Style for style-change action

    Returns:
        Complete edit instruction
    """
    base_prompt = ACTION_PRESETS.get(action, "")

    # Handle special cases
    if action == "change_style" and style:
        style_name = get_style_presets().get(style, style)
        base_prompt = base_prompt.format(style=style_name)
    elif action in ["add_elements", "remove_object"] and custom_prompt:
        base_prompt = base_prompt.format(prompt=custom_prompt)
    elif custom_prompt:
        # For other actions, append custom instructions
        base_prompt = f"{base_prompt} Additional instructions: {custom_prompt}"

    return base_prompt


def generate_image(
    prompt: str,
    style: str = "photorealistic",
    aspect_ratio: str = "1:1",
    size: str = "1k"
) -> Tuple[bytes, str]:
    """
    Generate an image from text prompt using Imagen 3.

    Args:
        prompt: Text description of the image to generate
        style: Style preset name
        aspect_ratio: Aspect ratio (1:1, 4:5, 9:16, 16:9)
        size: Image size (1k, 2k, 4k)

    Returns:
        Tuple of (image_bytes, mime_type)

    Raises:
        AIImageError: If generation fails
    """
    try:
        client = _get_gemini_client()

        # Build full prompt with style
        full_prompt = _build_generation_prompt(prompt, style)

        # Generate image using Imagen 4
        response = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=full_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                person_generation="allow_adult",
            )
        )

        # Extract image data
        if not response.generated_images:
            raise AIImageError("No image generated. Try rephrasing your prompt.")

        generated_image = response.generated_images[0]

        # Return image bytes and mime type
        return generated_image.image.image_bytes, "image/png"

    except AIImageError:
        raise
    except Exception as e:
        raise AIImageError(f"Image generation failed: {str(e)}")


def edit_image(
    image_path: Path,
    action: str,
    custom_prompt: Optional[str] = None,
    style: Optional[str] = None
) -> Tuple[bytes, str]:
    """
    Edit an existing image using Gemini 2.5 Flash Image.

    Args:
        image_path: Path to input image
        action: Action preset name
        custom_prompt: Optional custom instructions
        style: Optional style for style-change action

    Returns:
        Tuple of (image_bytes, mime_type)

    Raises:
        AIImageError: If editing fails
    """
    try:
        client = _get_gemini_client()

        # Read image file
        if not image_path.exists():
            raise AIImageError("Image file not found")

        image_bytes = image_path.read_bytes()

        # Determine mime type
        suffix = image_path.suffix.lower()
        mime_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }
        input_mime_type = mime_type_map.get(suffix, "image/jpeg")

        # Create image part
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=input_mime_type
        )

        # Build edit prompt
        edit_instruction = _build_edit_prompt(action, custom_prompt, style)

        # Edit image using Gemini 3 Pro Image (Nano Banana Pro)
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[image_part, edit_instruction],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )

        # Extract edited image data
        if not response.candidates:
            raise AIImageError("Image editing failed. Try different instructions.")

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data, part.inline_data.mime_type

        raise AIImageError("No image data in response")

    except AIImageError:
        raise
    except Exception as e:
        raise AIImageError(f"Image editing failed: {str(e)}")


def check_api_key_configured() -> bool:
    """
    Check if Google API key is configured.

    Returns:
        True if API key is set, False otherwise
    """
    return bool(os.getenv("GOOGLE_API_KEY"))
