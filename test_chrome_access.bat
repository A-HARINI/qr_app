@echo off
echo ========================================
echo Testing Server Access
echo ========================================
echo.
echo This will test if your server is accessible
echo.

echo [1] Testing if server is running...
netstat -ano | findstr :5000
if errorlevel 1 (
    echo [ERROR] Server is NOT running!
    echo.
    echo Start the server first:
    echo    python app.py
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Port 5000 is in use - server might be running
)

echo.
echo [2] Testing server response...
curl -s http://127.0.0.1:5000 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Server might not be responding
    echo Try accessing in browser: http://127.0.0.1:5000
) else (
    echo [OK] Server is responding!
)

echo.
echo [3] Opening browser...
echo.
echo If Chrome shows "Check your Internet connection":
echo   1. Make sure URL is: http://127.0.0.1:5000 (not https://)
echo   2. Disable Chrome proxy settings
echo   3. Try Firefox or Edge instead
echo.

start http://127.0.0.1:5000

echo.
echo Browser opened. Check if page loads.
echo.
pause




