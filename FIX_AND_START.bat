@echo off
title Flask Server - FIX AND START
color 0A
cls
echo.
echo ================================================================
echo           FIXING AND STARTING FLASK SERVER
echo ================================================================
echo.
echo This script will:
echo   1. Check if everything is OK
echo   2. Fix common issues
echo   3. Start the server
echo.
echo ================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python first!
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Flask is not installed
    echo Installing Flask...
    pip install flask
    if errorlevel 1 (
        echo [ERROR] Failed to install Flask
        pause
        exit /b 1
    )
    echo [OK] Flask installed
) else (
    echo [OK] Flask is installed
)
echo.

REM Check if port 5000 is in use
netstat -ano | findstr :5000 >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 5000 is already in use
    echo.
    echo To fix this:
    echo   1. Close other Python/Flask windows
    echo   2. Or run: netstat -ano ^| findstr :5000
    echo   3. Then: taskkill /PID ^<PID^> /F
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" (
        exit /b 1
    )
) else (
    echo [OK] Port 5000 is available
)
echo.

echo ================================================================
echo Starting Flask server...
echo ================================================================
echo.
echo IMPORTANT:
echo   - Keep this window OPEN
echo   - When you see "Running on http://0.0.0.0:5000"
echo     the server is ready!
echo   - Then open browser: http://127.0.0.1:5000
echo.
echo ================================================================
echo.

python diagnose_and_start.py

echo.
echo ================================================================
echo Server stopped.
echo ================================================================
pause




