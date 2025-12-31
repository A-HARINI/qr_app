@echo off
title Complete Mobile Access Fix - Comprehensive Solution
color 0C
mode con: cols=100 lines=45
cls
echo.
echo ================================================================
echo       COMPLETE MOBILE ACCESS FIX - COMPREHENSIVE SOLUTION
echo ================================================================
echo.
echo This will diagnose and fix ALL common mobile access issues.
echo.
pause
cls

echo.
echo ================================================================
echo                    STEP 1: STOPPING SERVER
echo ================================================================
echo.
echo Checking for running server processes...
tasklist | findstr /i python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Python processes found. Stopping them...
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo [OK] Python processes stopped
) else (
    echo [OK] No Python processes running
)
echo.

echo ================================================================
echo              STEP 2: CONFIGURING WINDOWS FIREWALL
echo ================================================================
echo.

echo Creating firewall rule for port 5000...
netsh advfirewall firewall delete rule name="Python Flask Server Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="Python Flask Server Port 5000" dir=in action=allow protocol=TCP localport=5000 enable=yes >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Firewall rule for port 5000 created
) else (
    echo [WARNING] Could not create firewall rule automatically
    echo           You may need Administrator privileges
)

echo.
echo Creating firewall rule for Python executable...
where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "delims=" %%i in ('where python') do (
        echo Creating rule for: %%i
        netsh advfirewall firewall delete rule name="Python" dir=in program="%%i" >nul 2>&1
        netsh advfirewall firewall add rule name="Python" dir=in action=allow program="%%i" enable=yes >nul 2>&1
    )
    echo [OK] Python application firewall rules created
) else (
    echo [INFO] Python not found in PATH, trying common locations...
    if exist "%LOCALAPPDATA%\Programs\Python\Python*\python.exe" (
        netsh advfirewall firewall add rule name="Python" dir=in action=allow program="%LOCALAPPDATA%\Programs\Python\Python*\python.exe" enable=yes >nul 2>&1
    )
    if exist "C:\Python*\python.exe" (
        netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Python*\python.exe" enable=yes >nul 2>&1
    )
    if exist "C:\Program Files\Python*\python.exe" (
        netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Program Files\Python*\python.exe" enable=yes >nul 2>&1
    )
)

echo.
echo ================================================================
echo                  STEP 3: GETTING NETWORK INFO
echo ================================================================
echo.
setlocal enabledelayedexpansion
echo Your network IP addresses:
echo.
set ip_count=0
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set /a ip_count+=1
    set ip=%%a
    set ip=!ip:~1!
    echo   [!ip_count!] !ip!
    echo      Mobile URL: http://!ip!:5000
    echo      Test URL:   http://!ip!:5000/test/network
    echo.
)
endlocal

echo ================================================================
echo              STEP 4: VERIFYING SERVER CONFIGURATION
echo ================================================================
echo.
echo Checking app.py configuration...
findstr /C:"host='0.0.0.0'" app.py >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server configured to bind to 0.0.0.0 (network accessible)
) else (
    echo [WARNING] Server may not be configured for network access
    echo          Checking app.run() configuration...
    findstr /C:"app.run" app.py | findstr "0.0.0.0"
    if %errorlevel% != 0 (
        echo [ERROR] Server not configured for network access!
        echo         Need to update app.py
    )
)
echo.

echo ================================================================
echo                  STEP 5: STARTING SERVER
echo ================================================================
echo.
echo Starting Flask server...
echo.
echo IMPORTANT: Keep this window open!
echo The server will start in a new window.
echo.
echo After server starts, look for:
echo   - "Running on http://0.0.0.0:5000"
echo   - "Network: http://[YOUR_IP]:5000"
echo.
pause

start "QR App Server" cmd /k "cd /d %~dp0 && python app.py"

echo.
echo ================================================================
echo                    STEP 6: WAITING FOR SERVER
echo ================================================================
echo.
echo Waiting 5 seconds for server to start...
timeout /t 5 /nobreak >nul

echo.
echo Checking if server is running...
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Server is running on port 5000!
    echo.
    netstat -ano | findstr ":5000"
) else (
    echo [ERROR] Server is not running on port 5000
    echo         Check the server window for error messages
)
echo.

echo ================================================================
echo                    STEP 7: TESTING CONNECTION
echo ================================================================
echo.
echo Testing local connection...
curl -s -o nul -w "HTTP Status: %%{http_code}\n" http://127.0.0.1:5000/test/network 2>nul
if %errorlevel% == 0 (
    echo [OK] Server responds to local requests
) else (
    echo [WARNING] Could not test local connection
    echo          (curl may not be installed - this is OK)
)
echo.

echo ================================================================
echo                    MOBILE TESTING INSTRUCTIONS
echo ================================================================
echo.
echo NOW TEST ON YOUR MOBILE PHONE:
echo.
echo 1. Make sure mobile is on SAME Wi-Fi network
echo.
echo 2. On mobile browser, try these URLs (use IP from above):
setlocal enabledelayedexpansion
set first_ip=1
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    if !first_ip! == 1 (
        set ip=%%a
        set ip=!ip:~1!
        echo    http://!ip!:5000
        echo    http://!ip!:5000/test/network
        set first_ip=0
    )
)
endlocal
echo.
echo 3. If you see "Cannot reach this page":
echo    - Check both devices are on same Wi-Fi
echo    - Try temporarily disabling Windows Firewall to test
echo    - Check router settings (disable AP Isolation)
echo.
echo 4. If you see the page but QR codes don't work:
echo    - Make sure server window shows network IP
echo    - QR codes should use network IP, not localhost
echo.

echo ================================================================
echo                    TROUBLESHOOTING CHECKLIST
echo ================================================================
echo.
echo [ ] Server window shows "Running on http://0.0.0.0:5000"
echo [ ] Firewall rule created (check Windows Firewall settings)
echo [ ] Both devices on same Wi-Fi network
echo [ ] Using correct IP address (from above)
echo [ ] Router doesn't have AP Isolation enabled
echo [ ] Server window is open (don't close it!)
echo.

echo ================================================================
echo                    MANUAL FIREWALL FIX (if needed)
echo ================================================================
echo.
echo If automatic firewall fix didn't work:
echo.
echo 1. Press Windows Key, type "Firewall"
echo 2. Click "Windows Defender Firewall"
echo 3. Click "Advanced settings"
echo 4. Click "Inbound Rules" -^> "New Rule"
echo 5. Select "Port" -^> Next
echo 6. Select "TCP" and enter "5000" -^> Next
echo 7. Select "Allow the connection" -^> Next
echo 8. Check all profiles (Domain, Private, Public) -^> Next
echo 9. Name it "Flask Server Port 5000" -^> Finish
echo.

echo ================================================================
echo.
echo Press any key to open the test network page in your browser...
pause >nul

setlocal enabledelayedexpansion
set first_ip=1
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    if !first_ip! == 1 (
        set ip=%%a
        set ip=!ip:~1!
        start http://!ip!:5000/test/network
        set first_ip=0
    )
)
endlocal

echo.
echo Test page opened in browser.
echo.
echo ================================================================
echo.
pause

