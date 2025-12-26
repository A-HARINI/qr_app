@echo off
echo ========================================
echo QR App - Starting Application
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Testing database connection...
python test_connection.py
if errorlevel 1 (
    echo.
    echo ERROR: Database connection failed!
    echo Please check FIX_MYSQL.md for instructions
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting Flask application...
echo.
echo ========================================
echo Server will start on http://127.0.0.1:5000
echo Press CTRL+C to stop the server
echo ========================================
echo.

python app.py

pause






