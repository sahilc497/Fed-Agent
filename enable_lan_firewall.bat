@echo off
title Configure Windows Firewall for Same-Wi-Fi Access

echo ===============================================================================
echo       FEDERATED AGENTIC MESH - WINDOWS FIREWALL CONFIGURATION (PORT 8000)
echo ===============================================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Administrative privileges are required.
    echo Please right-click 'enable_lan_firewall.bat' and choose 'Run as administrator'.
    echo.
    pause
    exit /b 1
)

echo [INFO] Adding inbound rules for Port 8000 (Backend) and Port 5173 (Frontend)...
netsh advfirewall firewall delete rule name="Federated Mesh Backend (8000)" >nul 2>&1
netsh advfirewall firewall delete rule name="Federated Mesh Frontend (5173)" >nul 2>&1
netsh advfirewall firewall add rule name="Federated Mesh Backend (8000)" dir=in action=allow protocol=TCP localport=8000 profile=private >nul
netsh advfirewall firewall add rule name="Federated Mesh Frontend (5173)" dir=in action=allow protocol=TCP localport=5173 profile=private >nul

echo.
echo [SUCCESS] Windows Firewall configured for ports 8000 and 5173!
echo Any device (Mac, laptop, phone) on the same Wi-Fi can now connect.
echo.
pause
