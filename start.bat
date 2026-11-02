@echo off
setlocal enabledelayedexpansion
title Federated Agentic Mesh - Launcher

echo ===============================================================================
echo                FEDERATED AGENTIC MESH - ENTERPRISE AI PLATFORM
echo               Four Departments - Local RAG - SQLite3 - Ollama
echo ===============================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 1. Check Python Virtual Environment
if not exist "%ROOT_DIR%venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at: %ROOT_DIR%venv
    echo Please ensure Python 3.10 is installed in .\venv before running.
    echo.
    pause
    exit /b 1
)

:: 2. Check Node.js and NPM
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] 'npm' was not found in your PATH. Frontend launch may fail.
)

:: 3. Detect Local Network IP for LAN / Wi-Fi Access
set "DETECTED_LAN_IP=127.0.0.1"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "TEMP_IP=%%a"
    set "TEMP_IP=!TEMP_IP: =!"
    if not "!TEMP_IP!"=="" (
        if not "!TEMP_IP:~0,4!"=="127." (
            if not "!TEMP_IP:~0,8!"=="169.254." (
                set "DETECTED_LAN_IP=!TEMP_IP!"
            )
        )
    )
)

:: 4. Verify Local Database Initialization
if not exist "%ROOT_DIR%backend\data\federated_mesh.db" (
    echo [INFO] Initializing SQLite database and synthetic department datasets...
    call "%ROOT_DIR%venv\Scripts\activate.bat"
    python "%ROOT_DIR%backend\scripts\generate_synthetic_datasets.py"
    python "%ROOT_DIR%backend\scripts\import_synthetic_to_sqlite.py"
)

:: 5. Check Ollama Local Answer Model Service
echo [INFO] Checking local Ollama service...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Starting local Ollama service with qwen3:8b...
    start "Federated Mesh - Ollama Service" cmd /c "ollama run qwen3:8b"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Ollama service is active.
)

:: 6. Launch FastAPI Backend on Port 8000 (Binding to 0.0.0.0 for LAN support)
echo [INFO] Starting FastAPI Backend on port 8000 (0.0.0.0)...
start "Federated Mesh - Backend (Port 8000)" cmd /k "title Backend Server [Port 8000] && cd /d "%ROOT_DIR%backend" && call "%ROOT_DIR%venv\Scripts\activate.bat" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 7. Launch React Vite Frontend on Port 5173
echo [INFO] Starting Vite Frontend on port 5173 (--host)...
start "Federated Mesh - Frontend (Port 5173)" cmd /k "title Frontend Server [Port 5173] && cd /d "%ROOT_DIR%frontend" && npm run dev -- --host"

:: 8. Wait for services to bind ports
echo.
echo [INFO] Initializing application services... Please wait...
timeout /t 4 /nobreak >nul

:: 9. Open Application in Default Browser
echo [INFO] Opening Web UI in default browser...
start http://localhost:5173

echo.
echo ===============================================================================
echo                      FEDERATED MESH IS NOW RUNNING!
echo ===============================================================================
echo.
echo  * Local Web App:     http://localhost:5173
echo  * FastAPI API Docs:  http://localhost:8000/docs
echo  * Same-Wi-Fi LAN IP: http://!DETECTED_LAN_IP!:5173
echo  * Database:          %ROOT_DIR%backend\data\federated_mesh.db
echo.
echo -------------------------------------------------------------------------------
echo  DEMO CREDENTIALS:
echo  - Administrator:     admin@mesh.internal         / AdminPass123!
echo  - Sales Lead:        sales.lead@mesh.internal    / SalesLead123!
echo  - HR Specialist:     hr.specialist@mesh.internal / HRPass123!
echo  - Finance Lead:      finance.manager@mesh.internal / FinanceLead123!
echo  - Operations Lead:   operations.specialist@mesh.internal / OpsSpec123!
echo -------------------------------------------------------------------------------
echo.
echo To stop all services cleanly, run 'stop.bat' or close the terminal windows.
echo.
pause
