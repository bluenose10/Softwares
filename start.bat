@echo off
echo Starting Media Toolkit...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo.

REM Start the server
echo Starting server...
echo Open your browser to: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.
uvicorn app.main:app --reload
