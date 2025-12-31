@echo off
title QR App Server - Output Screen
color 0A
mode con: cols=100 lines=40
cls
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo.
echo ================================================================
echo                    QR APP SERVER OUTPUT
echo ================================================================
echo.
echo Starting server... Please wait...
echo.
echo ================================================================
echo.
python app.py
echo.
echo ================================================================
echo Server stopped.
echo.
pause



