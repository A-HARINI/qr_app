@echo off
title Quick Start - QR App
color 0A
cls
echo.
echo ================================================================
echo                    QUICK START GUIDE
echo ================================================================
echo.
echo This will help you run the QR App project
echo.
echo ================================================================
echo.
echo STEP 1: Checking Python installation...
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python is installed
echo.

echo STEP 2: Checking required packages...
echo.
python -c "import flask; import qrcode; import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Some packages are missing!
    echo.
    echo Installing required packages...
    echo.
    pip install flask qrcode pillow
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install packages!
        echo Please run manually: pip install flask qrcode pillow
        pause
        exit /b 1
    )
    echo.
    echo [OK] Packages installed successfully
) else (
    echo [OK] All required packages are installed
)
echo.

echo ================================================================
echo STEP 3: Starting the server...
echo ================================================================
echo.
echo IMPORTANT: 
echo   - Keep this window OPEN
echo   - Wait for "* Running on http://0.0.0.0:5000" message
echo   - Then open browser: http://127.0.0.1:5000
echo.
echo ================================================================
echo.
pause

echo.
echo Starting server now...
echo.
python app.py

echo.
echo ================================================================
echo Server stopped.
echo ================================================================
pause



