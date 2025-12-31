@echo off
title Flask Server - DO NOT CLOSE THIS WINDOW
color 0A
echo.
echo ========================================
echo    FLASK SERVER - STARTING
echo ========================================
echo.
echo IMPORTANT: Keep this window open!
echo Closing this window will stop the server.
echo.
echo When you see "Running on http://0.0.0.0:5000"
echo Then open your browser and go to:
echo.
echo    http://127.0.0.1:5000
echo.
echo To stop the server, press CTRL+C in this window
echo.
echo ========================================
echo.
echo Starting server...
echo.

python app.py

echo.
echo ========================================
echo Server stopped.
echo ========================================
pause

