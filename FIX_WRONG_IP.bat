@echo off
title Fix Wrong IP Address Issue
color 0E
mode con: cols=90 lines=30
cls
echo.
echo ================================================================
echo              FIXING WRONG IP ADDRESS ISSUE
echo ================================================================
echo.
echo PROBLEM DETECTED:
echo   - Your computer IP: 192.168.1.10
echo   - Mobile trying to connect to: 192.168.1.100 (WRONG!)
echo.
echo ================================================================
echo.
echo SOLUTION: Use the CORRECT IP address on mobile
echo.
setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo YOUR CORRECT IP ADDRESS: !ip!
    echo.
    echo On your mobile phone, use this URL:
    echo.
    echo    http://!ip!:5000
    echo.
    echo NOT: http://192.168.1.100:5000
    echo.
    echo ================================================================
    echo.
    echo Creating QR code page with correct IP...
    echo.
    goto :found
)
:found
endlocal

echo Also checking firewall...
netsh advfirewall firewall show rule name="Python Flask Server Port 5000" | findstr "Enabled.*Yes" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Firewall rule exists and is enabled
) else (
    echo [FIXING] Creating firewall rule...
    netsh advfirewall firewall add rule name="Python Flask Server Port 5000" dir=in action=allow protocol=TCP localport=5000 enable=yes >nul 2>&1
    echo [OK] Firewall rule created
)

echo.
echo ================================================================
echo.
echo IMPORTANT: Make sure you use the CORRECT IP address!
echo.
pause

