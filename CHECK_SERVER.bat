@echo off
title Check Server Status
color 0E
cls
echo.
echo ================================================================
echo                    CHECKING SERVER STATUS
echo ================================================================
echo.

REM Check if port 5000 is in use
echo [1] Checking if port 5000 is in use...
netstat -ano | findstr :5000 >nul
if %errorlevel% == 0 (
    echo [OK] Port 5000 is in use - Server might be running!
    echo.
    echo Active connections on port 5000:
    netstat -ano | findstr :5000
    echo.
) else (
    echo [ERROR] Port 5000 is NOT in use - Server is NOT running!
    echo.
)

echo.
echo [2] Testing if server responds...
echo.
python -c "import urllib.request; import sys; try: urllib.request.urlopen('http://127.0.0.1:5000', timeout=2); print('[OK] Server is responding!'); sys.exit(0); except: print('[ERROR] Server is NOT responding'); print('[INFO] Server might not be running'); sys.exit(1)" 2>nul
if %errorlevel% == 0 (
    echo.
    echo ================================================================
    echo [SUCCESS] Server is running and accessible!
    echo ================================================================
    echo.
    echo You can access it at:
    echo   http://127.0.0.1:5000
    echo   http://127.0.0.1:5000/status
    echo.
    start http://127.0.0.1:5000
) else (
    echo.
    echo ================================================================
    echo [ERROR] Server is NOT running or NOT accessible
    echo ================================================================
    echo.
    echo SOLUTIONS:
    echo.
    echo 1. Start the server:
    echo    - Double-click: START_HERE_FOR_OUTPUT.bat
    echo    - Or run: python app.py
    echo.
    echo 2. Wait 5 seconds after starting
    echo.
    echo 3. Make sure you see this message in server window:
    echo    "* Running on http://0.0.0.0:5000"
    echo.
    echo 4. Then try accessing: http://127.0.0.1:5000
    echo.
)

echo.
echo ================================================================
pause



