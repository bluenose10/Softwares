"""Middleware to enforce usage limits and protect from abuse."""

from functools import wraps
from fastapi import Request, HTTPException
from app.services.usage_tracker import usage_tracker


def require_usage_limit(file_size_mb: float = 0):
    """
    Decorator to enforce usage limits on API endpoints.

    Args:
        file_size_mb: File size in MB (0 for operations without files)

    Raises:
        HTTPException: If user exceeds free tier limits
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Get client IP
            client_ip = request.client.host

            # Check if user can process
            can_process, reason = usage_tracker.can_process(client_ip, file_size_mb)

            if not can_process:
                raise HTTPException(
                    status_code=429,  # Too Many Requests
                    detail={
                        "error": "Usage limit exceeded",
                        "message": reason,
                        "upgrade_url": "/pricing"
                    }
                )

            # Increment usage count
            usage_tracker.increment_usage(client_ip)

            # Call the original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
