#!/usr/bin/env python3
"""Railway startup script that properly handles PORT environment variable."""
import os
import sys
import subprocess

def main():
    """Start uvicorn with proper PORT handling."""
    # Debug: Print all environment variables related to PORT
    print("=== ENVIRONMENT DEBUG ===")
    print(f"All env vars: {list(os.environ.keys())}")
    print(f"PORT env var: {os.environ.get('PORT', 'NOT SET')}")
    print("========================")

    # Get PORT from environment, default to 8000
    port = os.environ.get('PORT', '8000')

    # Validate port is a number
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            print(f"ERROR: PORT {port_num} is out of valid range (1-65535)")
            sys.exit(1)
    except ValueError:
        print(f"ERROR: PORT '{port}' is not a valid integer")
        sys.exit(1)

    print(f"Starting uvicorn on port {port_num}...")

    # Start uvicorn with the port
    cmd = [
        'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(port_num)
    ]

    print(f"Executing: {' '.join(cmd)}")

    # Execute uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: uvicorn exited with code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"ERROR: Failed to start uvicorn: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
