@echo off
title Show Previous Server Output
color 0B
cls
echo.
echo ================================================================
echo              PREVIOUS SERVER OUTPUT (Example)
echo ================================================================
echo.
echo This is what you should see when the server starts:
echo.
echo ================================================================
echo.

echo Starting QR App (SQLite Version)...
echo ==================================================
echo.
echo [INFO] Initializing database...
echo [OK] Database initialized successfully
echo.
echo Server starting on http://127.0.0.1:5000
echo Press CTRL+C to stop the server
echo ==================================================
echo.
echo ======================================================================
echo STARTING FLASK SERVER
echo ======================================================================
echo.
echo [OK] Port 5000 is available
echo.
echo [SUCCESS] Server will be accessible at:
echo   Local:    http://127.0.0.1:5000
echo   Network:  http://192.168.x.x:5000
echo.
echo [STATUS DASHBOARD]
echo   View output screen: http://127.0.0.1:5000/status
echo.
echo [MOBILE ACCESS]
echo   URL: http://192.168.x.x:5000
echo   Make sure mobile is on the SAME Wi-Fi network!
echo.
echo [TEST ENDPOINTS]
echo   Network test: http://192.168.x.x:5000/test/network
echo   Local test:   http://127.0.0.1:5000/test/network
echo.
echo [FIREWALL]
echo   If mobile cannot connect, check Windows Firewall:
echo   1. Allow Python through firewall
echo   2. Or create rule for port 5000
echo   3. See NETWORK_TROUBLESHOOTING.md for details
echo ======================================================================
echo.
echo  * Running on http://0.0.0.0:5000
echo  * Debug mode: on
echo.
echo ================================================================
echo.
echo To see REAL output from a running server:
echo   1. Start server: START_HERE_FOR_OUTPUT.bat
echo   2. Keep that window open to see live output
echo.
echo To save output to file for later viewing:
echo   1. Run: START_WITH_CAPTURE.bat
echo   2. Then view: VIEW_PREVIOUS_OUTPUT.bat
echo.
echo ================================================================
pause



