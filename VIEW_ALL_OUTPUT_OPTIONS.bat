@echo off
title View Output - All Options
color 0E
cls
echo.
echo ================================================================
echo              VIEW PREVIOUS OUTPUT - ALL OPTIONS
echo ================================================================
echo.
echo Choose how you want to view output:
echo.
echo ================================================================
echo.
echo [1] See Example Output (What it should look like)
echo     → Shows what the output should be
echo.
echo [2] View Saved Output Log (If you saved it before)
echo     → Shows output from server_output.log file
echo.
echo [3] View Startup Log (Server startup info)
echo     → Shows when server started and URLs
echo.
echo [4] Start Server and See Live Output
echo     → Start server and see output in real-time
echo.
echo [5] Start Server with Output Capture
echo     → Start server and save all output to file
echo.
echo ================================================================
echo.
choice /C 12345 /N /M "Choose option (1-5): "

if errorlevel 5 goto :option5
if errorlevel 4 goto :option4
if errorlevel 3 goto :option3
if errorlevel 2 goto :option2
if errorlevel 1 goto :option1

:option1
cls
echo.
echo Showing example output...
echo.
call SHOW_PREVIOUS_OUTPUT.bat
goto :end

:option2
cls
echo.
echo Checking for saved output log...
echo.
if exist server_output.log (
    echo [OK] Found server_output.log
    echo.
    echo Last 50 lines:
    echo ================================================================
    echo.
    powershell -Command "Get-Content server_output.log -Tail 50"
    echo.
    echo ================================================================
    echo.
    choice /C YN /M "Open full log in notepad"
    if errorlevel 2 goto :end
    if errorlevel 1 notepad server_output.log
) else (
    echo [WARNING] No output log file found!
    echo.
    echo To create output log:
    echo   1. Run: START_WITH_CAPTURE.bat
    echo   2. This will save all output to server_output.log
    echo.
)
goto :end

:option3
cls
echo.
echo Checking for startup log...
echo.
if exist server_startup.log (
    echo [OK] Found server_startup.log
    echo.
    echo Startup information:
    echo ================================================================
    echo.
    type server_startup.log
    echo.
    echo ================================================================
    echo.
    choice /C YN /M "Open full log in notepad"
    if errorlevel 2 goto :end
    if errorlevel 1 notepad server_startup.log
) else (
    echo [INFO] No startup log found yet.
    echo.
    echo Startup log is created automatically when server starts.
    echo Start the server to create this log.
    echo.
)
goto :end

:option4
cls
echo.
echo Starting server with live output...
echo.
call START_HERE_FOR_OUTPUT.bat
goto :end

:option5
cls
echo.
echo Starting server with output capture...
echo.
echo All output will be saved to: server_output.log
echo.
call START_WITH_CAPTURE.bat
goto :end

:end
pause



