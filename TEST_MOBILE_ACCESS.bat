@echo off
title Test Mobile Access - Network Diagnostic
color 0E
mode con: cols=100 lines=40
cls
echo.
echo ================================================================
echo            MOBILE ACCESS DIAGNOSTIC TOOL
echo ================================================================
echo.
echo This tool will help diagnose why mobile cannot access the server.
echo.
echo ================================================================
echo.
echo STEP 1: Checking if server is running...
echo.
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server is running on port 5000
    netstat -ano | findstr ":5000"
) else (
    echo [ERROR] Server is NOT running on port 5000
    echo.
    echo SOLUTION: Start the server first!
    echo   Double-click: START_HERE_FOR_OUTPUT.bat
    echo.
    pause
    exit /b
)
echo.
echo ================================================================
echo.
echo STEP 2: Checking server binding...
echo.
netstat -ano | findstr "0.0.0.0:5000" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server is bound to 0.0.0.0 (accessible from network)
) else (
    echo [WARNING] Server may not be bound to 0.0.0.0
    echo          Check server output for "Running on http://0.0.0.0:5000"
)
echo.
echo ================================================================
echo.
echo STEP 3: Getting your network IP address...
echo.
setlocal enabledelayedexpansion
echo Your network IP addresses:
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo   - !ip!
    echo   - Mobile URL: http://!ip!:5000
)
endlocal
echo.
echo ================================================================
echo.
echo STEP 4: Checking Windows Firewall...
echo.
netsh advfirewall firewall show rule name="Python Flask Server Port 5000" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Firewall rule exists for port 5000
) else (
    echo [WARNING] Firewall rule not found for port 5000
    echo.
    echo SOLUTION: Run FIX_MOBILE_ACCESS.bat to create firewall rule
)
echo.
netsh advfirewall firewall show rule name="Python" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python application firewall rule exists
) else (
    echo [INFO] Python application rule not found (may still work)
)
echo.
echo ================================================================
echo.
echo STEP 5: Testing local connection...
echo.
curl -s http://127.0.0.1:5000/test/network >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server responds to local requests
) else (
    echo [ERROR] Server does not respond to local requests
    echo         Server may not be running properly
)
echo.
echo ================================================================
echo.
echo MOBILE TESTING INSTRUCTIONS:
echo.
echo 1. Make sure your mobile phone is on the SAME Wi-Fi network
echo.
echo 2. On your mobile browser, try opening:
setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo    http://!ip!:5000
    echo    http://!ip!:5000/test/network
    goto :done
)
:done
endlocal
echo.
echo 3. If you see "Cannot reach this page" or "Site cannot be reached":
echo    - Check Windows Firewall (run FIX_MOBILE_ACCESS.bat)
echo    - Check router settings (disable AP Isolation)
echo    - Try temporarily disabling Windows Firewall to test
echo.
echo 4. If you see the page but QR codes don't work:
echo    - Make sure server shows "Network: http://[IP]:5000" in output
echo    - Check that QR codes use the network IP, not localhost
echo.
echo ================================================================
echo.
echo QUICK FIXES:
echo.
echo 1. Fix Firewall:     FIX_MOBILE_ACCESS.bat
echo 2. Restart Server:   START_HERE_FOR_OUTPUT.bat
echo 3. Check Network:    Open http://[YOUR_IP]:5000/test/network on mobile
echo.
echo ================================================================
echo.
pause

