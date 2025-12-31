@echo off
title Fix Mobile Access - Windows Firewall Configuration
color 0B
mode con: cols=90 lines=35
cls
echo.
echo ================================================================
echo          FIX MOBILE ACCESS - Windows Firewall Setup
echo ================================================================
echo.
echo This script will help you allow mobile devices to access
echo the Flask server on port 5000.
echo.
echo ================================================================
echo.
echo STEP 1: Checking current firewall rules...
echo.
netshell show rule name="Python" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python firewall rule exists
) else (
    echo [INFO] Python firewall rule not found - will create it
)
echo.
echo ================================================================
echo.
echo STEP 2: Creating firewall rule for Python on port 5000...
echo.
echo Creating inbound rule for Python...
netsh advfirewall firewall add rule name="Python Flask Server Port 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Firewall rule created successfully!
) else (
    echo [WARNING] Could not create rule automatically
    echo           You may need to run this as Administrator
)
echo.
echo ================================================================
echo.
echo STEP 3: Checking if Python is allowed through firewall...
echo.
netsh advfirewall firewall add rule name="Python" dir=in action=allow program="%LOCALAPPDATA%\Programs\Python\Python*\python.exe" enable=yes >nul 2>&1
netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Python*\python.exe" enable=yes >nul 2>&1
netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Program Files\Python*\python.exe" enable=yes >nul 2>&1
echo [OK] Python application rules added
echo.
echo ================================================================
echo.
echo STEP 4: Getting your network IP address...
echo.
setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo [INFO] Your network IP: !ip!
    echo [INFO] Mobile should access: http://!ip!:5000
    goto :found
)
:found
endlocal
echo.
echo ================================================================
echo.
echo MANUAL FIREWALL CONFIGURATION (if needed):
echo.
echo If the automatic setup didn't work, do this manually:
echo.
echo 1. Press Windows Key, type "Firewall"
echo 2. Click "Windows Defender Firewall"
echo 3. Click "Advanced settings" (on the left)
echo 4. Click "Inbound Rules" (on the left)
echo 5. Click "New Rule..." (on the right)
echo 6. Select "Port" - Next
echo 7. Select "TCP" and enter "5000" - Next
echo 8. Select "Allow the connection" - Next
echo 9. Check all profiles (Domain, Private, Public) - Next
echo 10. Name it "Flask Server Port 5000" - Finish
echo.
echo ================================================================
echo.
echo TESTING:
echo.
echo 1. Make sure server is running (START_HERE_FOR_OUTPUT.bat)
echo 2. On mobile, try: http://[YOUR_IP]:5000
echo    (Replace [YOUR_IP] with the IP shown above)
echo 3. If still not working, check:
echo    - Both devices on same Wi-Fi network
echo    - Router doesn't have "AP Isolation" enabled
echo    - Windows Firewall is not blocking (check manually)
echo.
echo ================================================================
echo.
pause

