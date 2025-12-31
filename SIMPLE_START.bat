@echo off
title Simple Server Start
color 0B
cls
echo.
echo ================================================================
echo                    SIMPLE SERVER START
echo ================================================================
echo.
echo Starting server...
echo.
echo IMPORTANT:
echo   - Keep this window OPEN
echo   - Wait for "Running on http://0.0.0.0:5000" message
echo   - Then open browser: http://127.0.0.1:5000
echo.
echo ================================================================
echo.
python app.py
pause



