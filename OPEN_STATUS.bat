@echo off
echo Opening Server Status Dashboard...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000/status
echo.
echo Status page should open in your browser.
echo.
echo If page doesn't load:
echo   1. Make sure server is running (python app.py)
echo   2. Wait a few seconds and try again
echo.
pause




