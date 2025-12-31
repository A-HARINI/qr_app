@echo off
title Test Output Screen
color 0B
cls
echo.
echo ================================================================
echo                    TESTING OUTPUT DISPLAY
echo ================================================================
echo.
echo This will show you what server output looks like...
echo.
echo ================================================================
echo.
echo [INFO] Starting QR App (SQLite Version)...
echo ================================================================
echo.
echo [INFO] Initializing database...
echo [OK] Database initialized successfully
echo.
echo ================================================================
echo.
echo [INFO] Starting Flask Server...
echo ================================================================
echo.
echo [OK] Port 5000 is available
echo.
echo [SUCCESS] Server will be accessible at:
echo   Local:    http://127.0.0.1:5000
echo   Network:  http://192.168.1.100:5000
echo.
echo [STATUS DASHBOARD]
echo   View output screen: http://127.0.0.1:5000/status
echo.
echo [MOBILE ACCESS]
echo   URL: http://192.168.1.100:5000
echo   Make sure mobile is on the SAME Wi-Fi network!
echo.
echo ================================================================
echo.
echo [INFO] To see REAL server output:
echo   1. Double-click: START_HERE_FOR_OUTPUT.bat
echo   2. Or run: python app.py
echo.
echo [INFO] To see web-based output screen:
echo   1. Start server (python app.py)
echo   2. Open: http://127.0.0.1:5000/status
echo.
echo ================================================================
echo.
pause



