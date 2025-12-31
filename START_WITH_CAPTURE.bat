@echo off
title Server with Output Capture
color 0A
cls
echo.
echo ================================================================
echo        STARTING SERVER WITH OUTPUT CAPTURE
echo ================================================================
echo.
echo All server output will be saved to: server_output.log
echo.
echo You can view previous output anytime by running:
echo   VIEW_PREVIOUS_OUTPUT.bat
echo.
echo ================================================================
echo.
python capture_output.py
pause



