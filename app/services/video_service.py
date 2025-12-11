"""Video processing service using FFmpeg."""

import json
import subprocess
import zipfile
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_video_duration(video_path: Path) -> float:
    """
    Get video duration in seconds using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds

    Raises:
        ValueError: If duration cannot be determined
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise ValueError("Failed to get video duration")

        duration = float(result.stdout.strip())
        return duration

    except (subprocess.TimeoutExpired, ValueError) as e:
        raise ValueError(f"Failed to get video duration: {str(e)}")


def get_video_info(video_path: Path) -> Dict:
    """
    Get detailed video information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video metadata

    Raises:
        ValueError: If video info cannot be retrieved
    """
    try:
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
        format_info = data.get("format", {})

        duration = float(format_info.get("duration", 0))
        size = int(format_info.get("size", 0))

        # Find video stream
        video_codec = None
        width = 0
        height = 0

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_codec = stream.get("codec_name", "unknown")
                width = stream.get("width", 0)
                height = stream.get("height", 0)
                break

        return {
            "filename": video_path.name,
            "duration": duration,
            "duration_formatted": format_duration(duration),
            "size": size,
            "video_codec": video_codec or "unknown",
            "resolution": f"{width}x{height}" if width and height else "unknown"
        }

    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to get video info: {str(e)}")


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


def calculate_split_times(duration: float, num_parts: int) -> List[Tuple[float, float]]:
    """
    Calculate split times for dividing video into equal parts.

    Args:
        duration: Total video duration in seconds
        num_parts: Number of parts to split into

    Returns:
        List of (start_time, end_time) tuples in seconds
    """
    if num_parts < 2:
        raise ValueError("Number of parts must be at least 2")
    if num_parts > 20:
        raise ValueError("Number of parts cannot exceed 20")

    part_duration = duration / num_parts
    split_times = []

    for i in range(num_parts):
        start_time = i * part_duration
        end_time = (i + 1) * part_duration
        split_times.append((start_time, end_time))

    return split_times


def split_video(
    video_path: Path,
    num_parts: int,
    output_dir: Path,
    use_stream_copy: bool = True
) -> List[Path]:
    """
    Split video into multiple equal parts using FFmpeg.

    Args:
        video_path: Path to input video
        num_parts: Number of parts to split into (2-20)
        output_dir: Directory to save output files
        use_stream_copy: Use stream copy for fast splitting (fallback to re-encode if fails)

    Returns:
        List of paths to output video files

    Raises:
        ValueError: If splitting fails
        RuntimeError: If FFmpeg is not installed
    """
    if not check_ffmpeg_installed():
        raise RuntimeError("FFmpeg is not installed")

    if num_parts < 2 or num_parts > 20:
        raise ValueError("Number of parts must be between 2 and 20")

    # Get video duration
    duration = get_video_duration(video_path)

    # Calculate split times
    split_times = calculate_split_times(duration, num_parts)

    # Split video
    output_paths = []
    base_name = video_path.stem
    extension = video_path.suffix

    for i, (start_time, end_time) in enumerate(split_times, 1):
        output_filename = f"{base_name}_part{i}{extension}"
        output_path = output_dir / output_filename

        segment_duration = end_time - start_time

        # Try stream copy first (fast, no quality loss)
        if use_stream_copy:
            success = _split_segment_stream_copy(
                video_path,
                output_path,
                start_time,
                segment_duration
            )

            if success:
                output_paths.append(output_path)
                continue

        # Fallback to re-encoding
        success = _split_segment_reencode(
            video_path,
            output_path,
            start_time,
            segment_duration
        )

        if success:
            output_paths.append(output_path)
        else:
            # Cleanup partial files
            for path in output_paths:
                path.unlink(missing_ok=True)
            raise ValueError(f"Failed to split video at part {i}")

    return output_paths


def _split_segment_stream_copy(
    input_path: Path,
    output_path: Path,
    start_time: float,
    duration: float
) -> bool:
    """
    Split a video segment using stream copy (fast, no re-encoding).

    Args:
        input_path: Input video path
        output_path: Output video path
        start_time: Start time in seconds
        duration: Segment duration in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        command = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c", "copy",  # Stream copy (no re-encoding)
            "-avoid_negative_ts", "make_zero",  # Fix timestamp issues
            str(output_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max per part
        )

        # Check if output file exists and has reasonable size
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            return True

        # Stream copy failed, cleanup
        output_path.unlink(missing_ok=True)
        return False

    except (subprocess.TimeoutExpired, Exception):
        output_path.unlink(missing_ok=True)
        return False


def _split_segment_reencode(
    input_path: Path,
    output_path: Path,
    start_time: float,
    duration: float
) -> bool:
    """
    Split a video segment with re-encoding (slower, but more reliable).

    Args:
        input_path: Input video path
        output_path: Output video path
        start_time: Start time in seconds
        duration: Segment duration in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        command = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",  # Re-encode video
            "-preset", "medium",
            "-crf", "23",  # Quality (lower = better, 18-28 range)
            "-c:a", "aac",  # Re-encode audio
            "-b:a", "128k",
            str(output_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max per part
        )

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            return True

        output_path.unlink(missing_ok=True)
        return False

    except (subprocess.TimeoutExpired, Exception):
        output_path.unlink(missing_ok=True)
        return False


def create_video_zip(video_paths: List[Path], zip_path: Path) -> Path:
    """
    Create a ZIP archive from multiple video files.

    Args:
        video_paths: List of video file paths
        zip_path: Output ZIP file path

    Returns:
        Path to created ZIP file
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for video_path in video_paths:
            zipf.write(video_path, video_path.name)

    return zip_path


def validate_video_file(file_path: Path) -> bool:
    """
    Validate if a file is a supported video.

    Args:
        file_path: Path to file

    Returns:
        True if file is a valid video
    """
    if not file_path.exists():
        return False

    try:
        # Try to get duration - if it works, it's a valid video
        duration = get_video_duration(file_path)
        return duration > 0
    except Exception:
        return False


# ============================================================================
# VIDEO COMPRESSION FUNCTIONS
# ============================================================================

def _get_crf_for_preset(preset: str) -> int:
    """
    Get CRF value for quality preset.

    CRF (Constant Rate Factor) scale: 0-51
    - Lower = better quality, larger file
    - Higher = worse quality, smaller file

    Args:
        preset: Quality preset (low/medium/high)

    Returns:
        CRF value
    """
    crf_map = {
        "low": 28,      # Smaller file, lower quality
        "medium": 23,   # Balanced (default)
        "high": 18      # Larger file, higher quality
    }
    return crf_map.get(preset.lower(), 23)


def compress_target_size(
    video_path: Path,
    target_size_mb: float,
    output_path: Path,
    audio_bitrate_kbps: int = 128
) -> Path:
    """
    Compress video to target file size using two-pass encoding.

    Two-pass encoding provides accurate bitrate targeting for precise file size.

    Args:
        video_path: Input video path
        target_size_mb: Target output size in MB
        output_path: Output video path
        audio_bitrate_kbps: Audio bitrate in kbps (default 128)

    Returns:
        Path to compressed video

    Raises:
        ValueError: If compression fails
        RuntimeError: If FFmpeg is not installed
    """
    if not check_ffmpeg_installed():
        raise RuntimeError("FFmpeg is not installed")

    # Get video duration
    duration = get_video_duration(video_path)

    # Calculate target video bitrate
    # Formula: ((target_size_mb * 8192) / duration_seconds) - audio_bitrate_kbps
    target_bitrate_kbps = ((target_size_mb * 8192) / duration) - audio_bitrate_kbps

    if target_bitrate_kbps < 100:
        raise ValueError("Target size too small - would result in unplayable video")

    # Use temp directory for two-pass log files
    with tempfile.TemporaryDirectory() as temp_dir:
        passlogfile = Path(temp_dir) / "ffmpeg2pass"

        # Two-pass encoding for accurate bitrate targeting
        success = _run_two_pass_encode(
            video_path,
            output_path,
            target_bitrate_kbps,
            audio_bitrate_kbps,
            passlogfile
        )

        if not success:
            raise ValueError("Video compression failed")

    return output_path


def compress_quality(
    video_path: Path,
    quality_preset: str,
    output_path: Path,
    audio_bitrate_kbps: int = 128
) -> Path:
    """
    Compress video using quality preset (CRF encoding).

    CRF (Constant Rate Factor) provides consistent quality throughout the video.

    Args:
        video_path: Input video path
        quality_preset: Quality preset (low/medium/high)
        output_path: Output video path
        audio_bitrate_kbps: Audio bitrate in kbps (default 128)

    Returns:
        Path to compressed video

    Raises:
        ValueError: If compression fails
        RuntimeError: If FFmpeg is not installed
    """
    if not check_ffmpeg_installed():
        raise RuntimeError("FFmpeg is not installed")

    crf = _get_crf_for_preset(quality_preset)

    try:
        command = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", f"{audio_bitrate_kbps}k",
            str(output_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode != 0 or not output_path.exists():
            raise ValueError(f"FFmpeg failed: {result.stderr}")

        return output_path

    except subprocess.TimeoutExpired:
        output_path.unlink(missing_ok=True)
        raise ValueError("Compression timed out (>1 hour)")
    except Exception as e:
        output_path.unlink(missing_ok=True)
        raise ValueError(f"Compression failed: {str(e)}")


def compress_resolution(
    video_path: Path,
    resolution: str,
    quality_preset: str,
    output_path: Path,
    audio_bitrate_kbps: int = 128
) -> Path:
    """
    Compress video by downscaling to target resolution.

    Maintains aspect ratio using scale filter: scale=-2:{height}
    The -2 ensures even dimensions (required by libx264).

    Args:
        video_path: Input video path
        resolution: Target resolution (2160p/1440p/1080p/720p/480p/360p)
        quality_preset: Quality preset (low/medium/high)
        output_path: Output video path
        audio_bitrate_kbps: Audio bitrate in kbps (default 128)

    Returns:
        Path to compressed video

    Raises:
        ValueError: If compression fails
        RuntimeError: If FFmpeg is not installed
    """
    if not check_ffmpeg_installed():
        raise RuntimeError("FFmpeg is not installed")

    # Map resolution to height
    resolution_map = {
        "2160p": 2160,
        "1440p": 1440,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360
    }

    height = resolution_map.get(resolution)
    if not height:
        raise ValueError(f"Invalid resolution: {resolution}")

    crf = _get_crf_for_preset(quality_preset)

    try:
        command = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vf", f"scale=-2:{height}",  # Maintain aspect ratio, ensure even dimensions
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", f"{audio_bitrate_kbps}k",
            str(output_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode != 0 or not output_path.exists():
            raise ValueError(f"FFmpeg failed: {result.stderr}")

        return output_path

    except subprocess.TimeoutExpired:
        output_path.unlink(missing_ok=True)
        raise ValueError("Compression timed out (>1 hour)")
    except Exception as e:
        output_path.unlink(missing_ok=True)
        raise ValueError(f"Compression failed: {str(e)}")


def estimate_output_size(
    video_path: Path,
    mode: str,
    target_size_mb: Optional[float] = None,
    quality_preset: Optional[str] = None,
    resolution: Optional[str] = None
) -> Dict:
    """
    Estimate output size without actually compressing.

    Provides rough estimates based on compression mode and settings.

    Args:
        video_path: Input video path
        mode: Compression mode (target_size/quality/resolution)
        target_size_mb: Target size for target_size mode
        quality_preset: Quality preset for quality/resolution mode
        resolution: Target resolution for resolution mode

    Returns:
        Dictionary with estimated size and reduction percentage

    Raises:
        ValueError: If parameters are invalid
    """
    info = get_video_info(video_path)
    original_size_mb = info["size"] / (1024 * 1024)

    estimated_size_mb = original_size_mb

    if mode == "target_size" and target_size_mb:
        estimated_size_mb = target_size_mb

    elif mode == "quality" and quality_preset:
        # Rough estimates based on typical CRF compression ratios
        compression_ratios = {
            "low": 0.3,    # ~70% reduction
            "medium": 0.5,  # ~50% reduction
            "high": 0.7     # ~30% reduction
        }
        ratio = compression_ratios.get(quality_preset.lower(), 0.5)
        estimated_size_mb = original_size_mb * ratio

    elif mode == "resolution" and resolution and quality_preset:
        # Get current resolution
        res_parts = info["resolution"].split("x")
        if len(res_parts) == 2:
            current_height = int(res_parts[1])

            # Map target resolution
            resolution_map = {
                "2160p": 2160,
                "1440p": 1440,
                "1080p": 1080,
                "720p": 720,
                "480p": 480,
                "360p": 360
            }
            target_height = resolution_map.get(resolution, current_height)

            # Resolution scaling factor (based on pixel count reduction)
            scale_factor = (target_height / current_height) ** 2

            # Quality factor
            quality_factors = {
                "low": 0.3,
                "medium": 0.5,
                "high": 0.7
            }
            quality_factor = quality_factors.get(quality_preset.lower(), 0.5)

            estimated_size_mb = original_size_mb * scale_factor * quality_factor
        else:
            # Fallback if resolution parsing fails
            estimated_size_mb = original_size_mb * 0.5

    reduction_pct = ((original_size_mb - estimated_size_mb) / original_size_mb) * 100

    return {
        "original_size_mb": round(original_size_mb, 2),
        "estimated_size_mb": round(estimated_size_mb, 2),
        "reduction_percent": round(reduction_pct, 1)
    }


def _run_two_pass_encode(
    input_path: Path,
    output_path: Path,
    video_bitrate_kbps: float,
    audio_bitrate_kbps: int,
    passlogfile: Path
) -> bool:
    """
    Run two-pass FFmpeg encoding for accurate bitrate targeting.

    Pass 1: Analyze video and create log file
    Pass 2: Encode video using log file for accurate bitrate control

    Args:
        input_path: Input video path
        output_path: Output video path
        video_bitrate_kbps: Target video bitrate in kbps
        audio_bitrate_kbps: Audio bitrate in kbps
        passlogfile: Path for two-pass log files (without extension)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Pass 1: Analysis
        command_pass1 = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", f"{int(video_bitrate_kbps)}k",
            "-pass", "1",
            "-passlogfile", str(passlogfile),
            "-an",  # No audio in pass 1
            "-f", "null",
            "NUL" if subprocess.os.name == "nt" else "/dev/null"  # Windows vs Unix
        ]

        result1 = subprocess.run(
            command_pass1,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result1.returncode != 0:
            return False

        # Pass 2: Encoding
        command_pass2 = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", f"{int(video_bitrate_kbps)}k",
            "-pass", "2",
            "-passlogfile", str(passlogfile),
            "-c:a", "aac",
            "-b:a", f"{audio_bitrate_kbps}k",
            str(output_path)
        ]

        result2 = subprocess.run(
            command_pass2,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result2.returncode == 0 and output_path.exists():
            return True

        output_path.unlink(missing_ok=True)
        return False

    except (subprocess.TimeoutExpired, Exception):
        output_path.unlink(missing_ok=True)
        return False
