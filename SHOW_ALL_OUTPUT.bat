@echo off
title Show All Server Output
color 0E
cls
echo.
echo ================================================================
echo                    ALL SERVER OUTPUT
echo ================================================================
echo.

if exist server_output.log (
    echo Opening full output log...
    echo.
    notepad server_output.log
) else (
    echo [WARNING] No output log file found!
    echo.
    echo To create output log:
    echo   1. Run: START_WITH_CAPTURE.bat
    echo   2. This will save all output to server_output.log
    echo.
    echo Current server output (if running):
    echo ================================================================
    echo.
    echo [INFO] If server is running, output appears in server window
    echo [INFO] To capture output to file, use START_WITH_CAPTURE.bat
    echo.
)

pause



