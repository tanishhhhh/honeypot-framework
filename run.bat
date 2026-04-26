@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ========================================
:: ML Honeypot Framework - Robust Orchestrator
:: ========================================
:: Usage: Double-click this file, or from CMD run:  run.bat
:: NOTE:  Do NOT paste this script into PowerShell.
::        If you must use PowerShell, run:  cmd /c run.bat
:: ========================================

echo.
echo ========================================
echo   ML Honeypot Framework - Auto Launch
echo ========================================
echo.

:: -- Admin Check --
net session >nul 2>&1
if errorlevel 1 (
    echo [WARN] Not running as Administrator. Firewall mitigation may fail.
    echo        Right-click run.bat and select "Run as Administrator".
    echo.
    timeout /t 3 /nobreak >nul
)

:: -- Step 1: Check Docker --
echo [1/8] Checking Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running or not in PATH!
    echo [FIX]  Start Docker Desktop and try again.
    pause & exit /b 1
)
echo       [OK] Docker Desktop is running.
echo.

:: -- Step 2: Check Python --
echo [2/8] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo [FIX]  Install Python 3.9+ and add to PATH.
    pause & exit /b 1
)
echo       [OK] Python is installed.
echo.

:: -- Step 3: Check Node.js --
echo [3/8] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo [FIX]  Install Node.js 18+ from https://nodejs.org
    pause & exit /b 1
)
echo       [OK] Node.js is installed.
echo.

:: -- Step 4: Validate .env --
echo [4/8] Validating Environment Configuration...
if not exist ".env" (
    echo       [WARN] .env file not found. Email alerts will be disabled.
    echo       [INFO] Copy .env.example to .env to enable alerts.
) else (
    findstr /C:"ALERT_EMAIL_PASSWORD=" .env >nul
    if errorlevel 1 (
        echo       [WARN] SMTP password not configured. Email alerts disabled.
    ) else (
        echo       [OK] Email alert configuration detected.
    )
)
echo.

:: -- Step 5: Start Docker Services --
echo [5/8] Starting Docker Compose Services...
docker compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers!
    echo [FIX]  Run: docker compose logs
    pause & exit /b 1
)
echo       [OK] Backend, Cowrie, and database services started.
echo.

:: -- Step 6: Wait for Healthchecks --
echo [6/8] Waiting for services to initialize (30 seconds)...
timeout /t 30 /nobreak >nul
docker compose ps
echo.

:: -- Step 7: Initialize Database Schema --
echo [7/8] Initializing Database Tables...
if exist "scripts\init_db.sql" (
    docker compose cp scripts\init_db.sql db:/tmp/init_db.sql >nul 2>&1
    docker compose exec -T db psql -U admin -d honeypot -f /tmp/init_db.sql >nul 2>&1
    if errorlevel 1 (
        echo       [WARN] DB init may have failed - tables may already exist.
    ) else (
        echo       [OK] Database schema verified.
    )
) else (
    echo       [WARN] scripts\init_db.sql not found. Skipping DB init.
    echo       [FIX]  Ensure scripts\init_db.sql exists in the project root.
)
echo.

:: -- Step 8: Launch Watcher + Vite --
echo [8/8] Launching Real-Time Classifier and Vite Frontend...

:: Launch watcher in new window
if exist "src\watchers\cowrie_watcher.py" (
    start "Live SOC Watcher" cmd /k python src\watchers\cowrie_watcher.py
    echo       [OK] Watcher service launched in new window.
) else (
    echo       [WARN] cowrie_watcher.py not found. Real-time classification disabled.
)

:: Install frontend dependencies if needed
echo       [INFO] Starting Vite Dev Server on port 5173...
if not exist "frontend\node_modules" (
    echo       [INFO] Installing frontend dependencies first-time setup...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

:: Start Vite in a new window
start "Vite Frontend" cmd /k "cd /d %~dp0frontend & npm run dev"
timeout /t 5 /nobreak >nul
start http://localhost:5173
echo       [OK] React SOC Dashboard opened at http://localhost:5173
echo.

:: -- Optional Attack Simulation --
set /p run_attack="Start live attack simulation? (Y/N): "
if /i "!run_attack!"=="Y" (
    if exist "attacks\test_cowrie_attacks.ps1" (
        echo       [INFO] Launching attack simulation...
        start "Attack Simulation" powershell -ExecutionPolicy Bypass -File .\attacks\test_cowrie_attacks.ps1
    ) else (
        echo       [WARN] Attack simulation script not found.
    )
)

:: -- Final Status --
echo.
echo ========================================
echo   [OK] System Fully Operational!
echo.
echo   Dashboard : http://localhost:5173  (Vite Dev Server)
echo   API       : http://localhost:5000
echo   Honeypot  : SSH on 2222 / Telnet on 2223
echo   Watcher   : Check 'Live SOC Watcher' window
echo   Frontend  : Check 'Vite Frontend' window
echo ========================================
echo.
echo Press any key to exit (services continue running in background).
pause >nul
exit /b 0

:: ========================================
:: MANUAL STARTUP (if run.bat fails)
:: ========================================
:: 1. Start Docker:
::      docker compose up -d
:: 2. Wait 30s, then init DB:
::      docker compose cp scripts/init_db.sql db:/tmp/init_db.sql
::      docker compose exec -T db psql -U admin -d honeypot -f /tmp/init_db.sql
:: 3. Start watcher (Admin terminal):
::      python src\watchers\cowrie_watcher.py
:: 4. Start frontend:
::      cd frontend && npm install && npm run dev
:: 5. Open browser:
::      http://localhost:5173
:: ========================================