@echo off
title Server Output Viewer
color 0B
cls
echo.
echo ================================================================
echo              SERVER OUTPUT VIEWER
echo ================================================================
echo.
echo This will:
echo   1. Start the Flask server
echo   2. Show all server output in this window
echo   3. Open the status dashboard in your browser
echo.
echo ================================================================
echo.
echo Starting server...
echo.

REM Start server and open status page after a delay
start /B python app.py
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000/status

echo.
echo Server started! Status page should open in your browser.
echo.
echo Keep this window open to see server output.
echo Press CTRL+C to stop the server.
echo.
echo ================================================================
echo.

python app.py

pause




