@echo off
title Start Server and Open Browser
color 0A
cls
echo.
echo ================================================================
echo              STARTING SERVER AND OPENING BROWSER
echo ================================================================
echo.
echo This will:
echo   1. Start the Flask server
echo   2. Wait 5 seconds for server to start
echo   3. Open browser automatically
echo.
echo ================================================================
echo.
echo Starting server in background...
echo.

REM Start server in background
start "QR App Server" /MIN python app.py

echo Waiting 5 seconds for server to start...
timeout /t 5 /nobreak >nul

echo.
echo Opening browser...
start http://127.0.0.1:5000

echo.
echo ================================================================
echo Server should be starting...
echo Browser should open automatically
echo.
echo If page doesn't load:
echo   1. Wait 10 more seconds
echo   2. Check server window (look for "Running on http://0.0.0.0:5000")
echo   3. Try: http://127.0.0.1:5000
echo.
echo ================================================================
echo.
echo To see server output, look for the minimized window:
echo "QR App Server"
echo.
pause



