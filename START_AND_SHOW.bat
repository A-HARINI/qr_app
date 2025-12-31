@echo off
title QR App Server
color 0B
cls
echo.
echo ================================================================
echo                    QR APP SERVER
echo ================================================================
echo.
echo Starting server...
echo.
echo IMPORTANT: Keep this window open to see server output!
echo.
echo After server starts, you will see:
echo   - Server URL
echo   - Network IP address
echo   - Status dashboard link
echo.
echo ================================================================
echo.
python app.py
echo.
echo ================================================================
echo Server stopped.
echo.
pause



