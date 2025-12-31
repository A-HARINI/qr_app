@echo off
title Show Correct IP Address for Mobile
color 0A
mode con: cols=80 lines=25
cls
echo.
echo ================================================================
echo              CORRECT IP ADDRESS FOR MOBILE
echo ================================================================
echo.
setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo.
    echo YOUR COMPUTER IP ADDRESS: !ip!
    echo.
    echo ================================================================
    echo.
    echo ON YOUR MOBILE PHONE, USE THIS URL:
    echo.
    echo    http://!ip!:5000
    echo.
    echo ================================================================
    echo.
    echo TEST URLS:
    echo    http://!ip!:5000/test/network
    echo    http://!ip!:5000
    echo.
    echo ================================================================
    echo.
    echo IMPORTANT:
    echo   - Make sure mobile is on SAME Wi-Fi network
    echo   - Use this EXACT IP: !ip!
    echo   - Do NOT use: 192.168.1.100 or any other IP
    echo.
    goto :found
)
:found
endlocal
echo.
pause

