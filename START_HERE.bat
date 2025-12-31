@echo off
title Flask Server - READ THIS WINDOW
color 0E
cls
echo.
echo ================================================================
echo                    STARTING FLASK SERVER
echo ================================================================
echo.
echo STEP 1: Starting server...
echo.
echo IMPORTANT: 
echo   - Keep this window OPEN
echo   - When you see "Running on http://0.0.0.0:5000" below,
echo     the server is ready!
echo   - Then open your browser and go to: http://127.0.0.1:5000
echo.
echo ================================================================
echo.

python app.py

echo.
echo ================================================================
echo Server stopped. Close this window.
echo ================================================================
pause




