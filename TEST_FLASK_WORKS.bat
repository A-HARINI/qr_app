@echo off
title Test if Flask Works
color 0B
cls
echo.
echo ================================================================
echo              TESTING IF FLASK WORKS
echo ================================================================
echo.
echo This will start a simple test server to verify Flask is working.
echo.
echo If you see a page saying "Server is Working!" then Flask is OK.
echo.
echo ================================================================
echo.
echo Starting test server on port 5001...
echo.
start http://127.0.0.1:5001
timeout /t 2 /nobreak >nul
python test_simple_server.py
pause



