"""Audio extraction service using FFmpeg."""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional


# Supported formats
SUPPORTED_VIDEO_FORMATS = [
    "mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "mpeg", "mpg", "3gp"
]

SUPPORTED_AUDIO_FORMATS = {
    "mp3": {"codec": "libmp3lame", "supports_bitrate": True},
    "aac": {"codec": "aac", "supports_bitrate": True},
    "wav": {"codec": "pcm_s16le", "supports_bitrate": False},
    "flac": {"codec": "flac", "supports_bitrate": False},
    "ogg": {"codec": "libvorbis", "supports_bitrate": True}
}

BITRATE_OPTIONS = [64, 128, 192, 256, 320]  # kbps


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and accessible.

    Returns:
        True if FFmpeg is available
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_ffprobe_installed() -> bool:
    """
    Check if FFprobe is installed and accessible.

    Returns:
        True if FFprobe is available
    """
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            timeout=5
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_supported_formats() -> Dict:
    """Get supported video inputs and audio outputs."""
    return {
        "video_inputs": SUPPORTED_VIDEO_FORMATS,
        "audio_outputs": list(SUPPORTED_AUDIO_FORMATS.keys()),
        "bitrate_options": BITRATE_OPTIONS,
        "formats_with_bitrate": [
            fmt for fmt, info in SUPPORTED_AUDIO_FORMATS.items()
            if info["supports_bitrate"]
        ]
    }


def get_video_info(video_path: Path) -> Dict:
    """
    Get information about a video file using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with duration, size, codec info

    Raises:
        RuntimeError: If FFprobe is not installed
        ValueError: If video cannot be read
    """
    if not check_ffprobe_installed():
        raise RuntimeError(
            "FFprobe is not installed. Please install FFmpeg to use this feature."
        )

    try:
        # Run ffprobe to get video info
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise ValueError("Failed to read video file")

        data = json.loads(result.stdout)

        # Extract format info
        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 0))
        size = int(format_info.get("size", 0))

        # Find video and audio streams
        video_codec = None
        audio_codec = None
        has_audio = False

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_codec:
                video_codec = stream.get("codec_name", "unknown")
            elif stream.get("codec_type") == "audio" and not audio_codec:
                audio_codec = stream.get("codec_name", "unknown")
                has_audio = True

        return {
            "filename": video_path.name,
            "duration": duration,
            "duration_formatted": format_duration(duration),
            "size": size,
            "video_codec": video_codec or "unknown",
            "audio_codec": audio_codec or "unknown",
            "has_audio": has_audio
        }

    except subprocess.TimeoutExpired:
        raise ValueError("Video analysis timed out")
    except json.JSONDecodeError:
        raise ValueError("Failed to parse video information")
    except Exception as e:
        raise ValueError(f"Failed to read video: {str(e)}")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to HH:MM:SS or MM:SS.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def extract_audio(
    video_path: Path,
    output_format: str,
    bitrate: int = 192,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Extract audio from a video file using FFmpeg.

    Args:
        video_path: Path to input video
        output_format: Target audio format (mp3, aac, wav, flac, ogg)
        bitrate: Bitrate in kbps (for lossy formats)
        output_dir: Output directory (defaults to same as video)

    Returns:
        Path to extracted audio file

    Raises:
        RuntimeError: If FFmpeg is not installed
        ValueError: If format is not supported or extraction fails
    """
    if not check_ffmpeg_installed():
        raise RuntimeError(
            "FFmpeg is not installed. Please install FFmpeg to use this feature."
        )

    output_format = output_format.lower()

    if output_format not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {output_format}")

    # Validate bitrate
    if bitrate not in BITRATE_OPTIONS:
        bitrate = 192  # Default

    # Get format info
    format_info = SUPPORTED_AUDIO_FORMATS[output_format]
    codec = format_info["codec"]

    # Determine output path
    if output_dir is None:
        output_dir = video_path.parent

    output_path = output_dir / f"{video_path.stem}.{output_format}"

    # Build FFmpeg command
    command = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", codec
    ]

    # Add bitrate for lossy formats
    if format_info["supports_bitrate"]:
        command.extend(["-ab", f"{bitrate}k"])

    # Add output path
    command.append(str(output_path))

    try:
        # Run FFmpeg
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )

        if result.returncode != 0:
            error_msg = result.stderr.lower()

            if "no such file" in error_msg or "does not exist" in error_msg:
                raise ValueError("Video file not found")
            elif "invalid" in error_msg or "could not find" in error_msg:
                raise ValueError("Video file is invalid or corrupted")
            elif "no audio" in error_msg or "stream not found" in error_msg:
                raise ValueError("Video does not contain an audio stream")
            else:
                raise ValueError(f"Audio extraction failed: {result.stderr}")

        if not output_path.exists():
            raise ValueError("Audio file was not created")

        return output_path

    except subprocess.TimeoutExpired:
        raise ValueError("Audio extraction timed out (file too large or corrupted)")
    except Exception as e:
        # Cleanup partial output
        if output_path.exists():
            output_path.unlink()
        raise


def validate_video_file(file_path: Path) -> bool:
    """
    Validate if a file is a supported video.

    Args:
        file_path: Path to file

    Returns:
        True if file is a valid supported video
    """
    extension = file_path.suffix.lower().lstrip('.')

    if extension not in SUPPORTED_VIDEO_FORMATS:
        return False

    # Basic validation using ffprobe
    if not check_ffprobe_installed():
        # If ffprobe not available, just check extension
        return True

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(file_path)
            ],
            capture_output=True,
            timeout=10
        )

        if result.returncode != 0:
            return False

        data = json.loads(result.stdout)
        # Check if it has at least one stream
        return len(data.get("streams", [])) > 0

    except Exception:
        return False
