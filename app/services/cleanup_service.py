"""File cleanup service for managing temporary files."""

import os
import time
from pathlib import Path
from typing import List
from datetime import datetime, timedelta


def get_file_age_hours(file_path: Path) -> float:
    """
    Get file age in hours.

    Args:
        file_path: Path to file

    Returns:
        Age in hours
    """
    if not file_path.exists():
        return 0.0

    file_time = file_path.stat().st_mtime
    current_time = time.time()
    age_seconds = current_time - file_time
    return age_seconds / 3600


def cleanup_old_files(
    directory: Path,
    max_age_hours: float = 1.0,
    extensions: List[str] = None
) -> int:
    """
    Clean up old files in a directory.

    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours (default: 1 hour)
        extensions: List of file extensions to clean (None = all files)

    Returns:
        Number of files deleted
    """
    if not directory.exists():
        return 0

    deleted_count = 0

    try:
        for file_path in directory.iterdir():
            if not file_path.is_file():
                continue

            # Check extension filter
            if extensions and file_path.suffix.lower() not in extensions:
                continue

            # Check age
            age_hours = get_file_age_hours(file_path)
            if age_hours > max_age_hours:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    # Skip files that can't be deleted (in use, permission issues, etc.)
                    continue

    except Exception:
        # Directory access issues
        pass

    return deleted_count


def cleanup_uploads_and_outputs(
    uploads_dir: Path,
    outputs_dir: Path,
    max_age_hours: float = 1.0
) -> dict:
    """
    Clean up old files from uploads and outputs directories.

    Args:
        uploads_dir: Uploads directory path
        outputs_dir: Outputs directory path
        max_age_hours: Maximum file age in hours (default: 1 hour)

    Returns:
        Dictionary with cleanup statistics
    """
    uploads_deleted = cleanup_old_files(uploads_dir, max_age_hours)
    outputs_deleted = cleanup_old_files(outputs_dir, max_age_hours)

    return {
        "uploads_deleted": uploads_deleted,
        "outputs_deleted": outputs_deleted,
        "total_deleted": uploads_deleted + outputs_deleted
    }


def get_directory_size(directory: Path) -> int:
    """
    Get total size of all files in directory (bytes).

    Args:
        directory: Directory path

    Returns:
        Total size in bytes
    """
    if not directory.exists():
        return 0

    total_size = 0

    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    continue
    except Exception:
        pass

    return total_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_cleanup_stats(uploads_dir: Path, outputs_dir: Path) -> dict:
    """
    Get statistics about temporary directories.

    Args:
        uploads_dir: Uploads directory path
        outputs_dir: Outputs directory path

    Returns:
        Dictionary with directory statistics
    """
    def count_files(directory: Path) -> int:
        if not directory.exists():
            return 0
        return sum(1 for f in directory.iterdir() if f.is_file())

    uploads_size = get_directory_size(uploads_dir)
    outputs_size = get_directory_size(outputs_dir)

    return {
        "uploads": {
            "file_count": count_files(uploads_dir),
            "size_bytes": uploads_size,
            "size_formatted": format_file_size(uploads_size)
        },
        "outputs": {
            "file_count": count_files(outputs_dir),
            "size_bytes": outputs_size,
            "size_formatted": format_file_size(outputs_size)
        },
        "total": {
            "file_count": count_files(uploads_dir) + count_files(outputs_dir),
            "size_bytes": uploads_size + outputs_size,
            "size_formatted": format_file_size(uploads_size + outputs_size)
        }
    }


def delete_file_safe(file_path: Path) -> bool:
    """
    Safely delete a file with error handling.

    Args:
        file_path: Path to file to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
    except Exception:
        pass
    return False


def delete_directory_contents(directory: Path) -> int:
    """
    Delete all files in a directory but keep the directory.

    Args:
        directory: Directory path

    Returns:
        Number of files deleted
    """
    if not directory.exists():
        return 0

    deleted_count = 0

    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                if delete_file_safe(file_path):
                    deleted_count += 1
    except Exception:
        pass

    return deleted_count
