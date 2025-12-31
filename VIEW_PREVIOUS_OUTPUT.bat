@echo off
title View Previous Server Output
color 0B
cls
echo.
echo ================================================================
echo              VIEWING PREVIOUS SERVER OUTPUT
echo ================================================================
echo.

if exist server_output.log (
    echo [OK] Found output log file!
    echo.
    echo Showing last 50 lines of output:
    echo ================================================================
    echo.
    powershell -Command "Get-Content server_output.log -Tail 50"
    echo.
    echo ================================================================
    echo.
    echo To see full output, open: server_output.log
    echo.
    choice /C YN /M "Open full log file in notepad"
    if errorlevel 2 goto :end
    if errorlevel 1 notepad server_output.log
) else (
    echo [WARNING] No output log file found!
    echo.
    echo This means the server hasn't been run with output capture yet.
    echo.
    echo To capture output:
    echo   1. Run: START_WITH_CAPTURE.bat
    echo   2. Or run: python capture_output.py
    echo.
    echo The output will be saved to: server_output.log
    echo.
)

:end
echo.
pause



