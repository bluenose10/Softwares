"""Image conversion service using Pillow."""

import io
import zipfile
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()


# Supported formats
SUPPORTED_INPUT_FORMATS = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WebP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
    "heic": "HEIF",
    "heif": "HEIF"
}

SUPPORTED_OUTPUT_FORMATS = {
    "png": "PNG",
    "jpg": "JPEG",
    "webp": "WebP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF"
}

# Formats that support quality parameter
QUALITY_FORMATS = {"jpg", "jpeg", "webp"}

# Formats that don't support alpha channel
NO_ALPHA_FORMATS = {"jpg", "jpeg", "bmp"}


def get_supported_formats() -> dict:
    """Get supported input and output formats."""
    return {
        "input": list(SUPPORTED_INPUT_FORMATS.keys()),
        "output": list(SUPPORTED_OUTPUT_FORMATS.keys()),
        "quality_supported": list(QUALITY_FORMATS)
    }


def convert_image(
    input_path: Path,
    output_format: str,
    quality: int = 85,
    optimize: bool = True
) -> Path:
    """
    Convert an image to a different format.

    Args:
        input_path: Path to input image
        output_format: Target format (png, jpg, webp, etc.)
        quality: Quality for lossy formats (1-100)
        optimize: Whether to optimize the output

    Returns:
        Path to converted image

    Raises:
        ValueError: If format is not supported
        IOError: If image cannot be read or written
    """
    output_format = output_format.lower().replace("jpeg", "jpg")

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")

    # Validate quality
    quality = max(1, min(100, quality))

    # Load image
    try:
        img = Image.open(input_path)
    except Exception as e:
        raise IOError(f"Failed to open image: {str(e)}")

    # Convert color mode if necessary
    img = _convert_color_mode(img, output_format)

    # Generate output path
    output_path = input_path.parent / f"{input_path.stem}.{output_format}"

    # Prepare save options
    save_kwargs = {
        "format": SUPPORTED_OUTPUT_FORMATS[output_format]
    }

    # Add quality for supported formats
    if output_format in QUALITY_FORMATS:
        save_kwargs["quality"] = quality

    # Add optimization
    if output_format == "png":
        save_kwargs["optimize"] = optimize
    elif output_format in QUALITY_FORMATS:
        save_kwargs["optimize"] = optimize

    # Save converted image
    try:
        img.save(output_path, **save_kwargs)
    except Exception as e:
        raise IOError(f"Failed to save image: {str(e)}")
    finally:
        img.close()

    return output_path


def _convert_color_mode(img: Image.Image, output_format: str) -> Image.Image:
    """
    Convert image color mode based on output format requirements.

    Args:
        img: PIL Image object
        output_format: Target format

    Returns:
        Image with appropriate color mode
    """
    # Handle palette mode (GIF, PNG with palette)
    if img.mode == "P":
        if "transparency" in img.info:
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

    # Convert RGBA to RGB for formats that don't support alpha
    if img.mode == "RGBA" and output_format in NO_ALPHA_FORMATS:
        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img.close()
        return background

    # Convert grayscale with alpha to RGBA
    if img.mode == "LA":
        img = img.convert("RGBA")

    # Convert grayscale to RGB if needed
    if img.mode == "L" and output_format in {"jpg", "webp"}:
        img = img.convert("RGB")

    # Convert CMYK to RGB
    if img.mode == "CMYK":
        img = img.convert("RGB")

    return img


def convert_multiple_images(
    input_paths: List[Path],
    output_format: str,
    quality: int = 85
) -> List[Tuple[Path, Path]]:
    """
    Convert multiple images to the same format.

    Args:
        input_paths: List of input image paths
        output_format: Target format
        quality: Quality for lossy formats

    Returns:
        List of tuples (input_path, output_path) for successful conversions
    """
    results = []

    for input_path in input_paths:
        try:
            output_path = convert_image(input_path, output_format, quality)
            results.append((input_path, output_path))
        except Exception as e:
            print(f"Failed to convert {input_path.name}: {str(e)}")
            # Continue with other images
            continue

    return results


def create_zip_archive(file_paths: List[Path], zip_path: Path) -> Path:
    """
    Create a ZIP archive from multiple files.

    Args:
        file_paths: List of file paths to include
        zip_path: Output ZIP file path

    Returns:
        Path to created ZIP file
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            zipf.write(file_path, file_path.name)

    return zip_path


def validate_image_file(file_path: Path) -> bool:
    """
    Validate if a file is a supported image.

    Args:
        file_path: Path to file

    Returns:
        True if file is a valid supported image
    """
    extension = file_path.suffix.lower().lstrip('.')

    if extension not in SUPPORTED_INPUT_FORMATS:
        return False

    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False
