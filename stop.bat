@echo off
title Federated Agentic Mesh - Stop Services

echo ===============================================================================
echo                FEDERATED AGENTIC MESH - STOPPING SERVICES
echo ===============================================================================
echo.

echo [INFO] Stopping FastAPI Backend (Port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Stopping Vite Frontend (Port 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Closing server windows...
taskkill /F /FI "WINDOWTITLE eq Backend Server [Port 8000]*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Frontend Server [Port 5173]*" >nul 2>&1

echo.
echo [OK] All Federated Agentic Mesh services have been stopped.
echo.
timeout /t 2 /nobreak >nul
