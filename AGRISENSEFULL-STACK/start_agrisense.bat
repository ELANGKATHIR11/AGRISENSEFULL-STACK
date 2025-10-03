@echo off
REM AgriSense Unified Server Startup Script for Windows
REM This script starts both frontend and backend on a single server

echo 🌾 Starting AgriSense Unified Server...
echo ==========================================

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at .venv
    echo Please ensure you have set up the Python virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set environment variables for optimal performance
set AGRISENSE_DISABLE_ML=1

REM Start the unified server
echo Starting AgriSense server...
echo Frontend will be served at: http://localhost:8004/ui
echo API documentation at: http://localhost:8004/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python start_agrisense.py %*

echo.
echo Server stopped.
pause