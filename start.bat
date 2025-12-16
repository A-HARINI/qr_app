@echo off
echo ========================================
echo   Starting Flask QR App
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Flask application...
echo.
echo Open your browser at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python app.py
pause



