@echo off
title Fix: Cannot Reach Page
color 0C
cls
echo.
echo ================================================================
echo           FIX: CANNOT REACH PAGE / SITE CANNOT BE REACHED
echo ================================================================
echo.
echo STEP 1: Checking if server is running...
echo.
netstat -ano | findstr :5000 >nul
if %errorlevel% == 0 (
    echo [OK] Port 5000 is in use - Server might be running
    echo.
    echo Testing connection...
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000', timeout=2); print('[OK] Server is responding!')" 2>nul
    if %errorlevel% == 0 (
        echo.
        echo [SUCCESS] Server is running and accessible!
        echo Opening browser...
        start http://127.0.0.1:5000
        goto :end
    )
) else (
    echo [ERROR] Server is NOT running!
)

echo.
echo ================================================================
echo STEP 2: Starting the server...
echo ================================================================
echo.
echo IMPORTANT: A new window will open with the server.
echo Keep that window OPEN!
echo.
echo Wait for this message in the server window:
echo   "* Running on http://0.0.0.0:5000"
echo.
echo Then come back here and press any key to continue...
echo.
pause

echo.
echo Starting server in new window...
start "QR App Server - DO NOT CLOSE" cmd /k "cd /d %~dp0 && python app.py"

echo.
echo Waiting 8 seconds for server to start...
timeout /t 8 /nobreak >nul

echo.
echo ================================================================
echo STEP 3: Testing connection...
echo ================================================================
echo.
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000', timeout=3); print('[SUCCESS] Server is now accessible!'); print('[INFO] Opening browser...')" 2>nul
if %errorlevel% == 0 (
    echo.
    echo Opening browser...
    start http://127.0.0.1:5000
    echo.
    echo ================================================================
    echo [SUCCESS] Server is running!
    echo ================================================================
    echo.
    echo You can now access:
    echo   http://127.0.0.1:5000
    echo   http://127.0.0.1:5000/status
    echo.
) else (
    echo.
    echo [WARNING] Server might still be starting...
    echo.
    echo Try these steps:
    echo   1. Check the server window - look for errors
    echo   2. Wait 5 more seconds
    echo   3. Manually open: http://127.0.0.1:5000
    echo   4. Make sure you see "Running on http://0.0.0.0:5000" in server window
    echo.
)

:end
echo.
echo ================================================================
echo TROUBLESHOOTING:
echo ================================================================
echo.
echo If page still doesn't load:
echo.
echo 1. Check server window is open and shows:
echo    "* Running on http://0.0.0.0:5000"
echo.
echo 2. Make sure URL is EXACTLY:
echo    http://127.0.0.1:5000
echo    (NOT https://, NOT localhost, NOT 127.0.0.1:5001)
echo.
echo 3. Try different browser (Chrome, Firefox, Edge)
echo.
echo 4. Check Windows Firewall:
echo    - Allow Python through firewall
echo    - Or temporarily disable firewall to test
echo.
echo 5. Check for errors in server window (red text)
echo.
echo ================================================================
pause



