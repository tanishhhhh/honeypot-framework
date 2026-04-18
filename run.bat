@echo off
setlocal enabledelayedexpansion

:: Color codes
call :colorEcho 0A "========================================"
call :colorEcho 0A "  ML Honeypot Framework - Auto Startup"
call :colorEcho 0A "========================================"
echo.

:: Step 1: Check Docker
call :colorEcho 0E "[1/6] Checking Docker Desktop..."
docker info >nul 2>&1
if errorlevel 1 (
    call :colorEcho 0C "ERROR: Docker Desktop is not running!"
    echo Please start Docker Desktop and run this script again.
    pause
    exit /b 1
)
call :colorEcho 02 "Docker Desktop is running."
echo.

:: Step 2: Check Python
call :colorEcho 0E "[2/6] Checking Python..."
python --version >nul 2>&1
if errorlevel 1 (
    call :colorEcho 0C "ERROR: Python is not installed or not in PATH!"
    pause
    exit /b 1
)
call :colorEcho 02 "Python is installed."
echo.

:: Step 3: Initialize Database
call :colorEcho 0E "[3/6] Initializing PostgreSQL database..."
docker compose exec -T db psql -U admin -d honeypot -c "CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, duration FLOAT, orig_bytes INTEGER, resp_bytes INTEGER, orig_pkts INTEGER, resp_pkts INTEGER, proto VARCHAR(10), conn_state VARCHAR(10), history VARCHAR(50), source_ip VARCHAR(45), dest_ip VARCHAR(45), prediction INTEGER, class_name VARCHAR(50), confidence FLOAT, severity VARCHAR(20), attack_type VARCHAR(100), mitigation TEXT[]);" >nul 2>&1
if errorlevel 1 (
    call :colorEcho 01 "WARNING: Database initialization skipped (container may not be ready yet)"
) else (
    call :colorEcho 02 "Database initialized successfully."
)
echo.

:: Step 4: Start Docker Services
call :colorEcho 0E "[4/6] Starting Docker containers..."
docker compose up -d --build
if errorlevel 1 (
    call :colorEcho 0C "ERROR: Failed to start Docker containers!"
    docker compose down
    pause
    exit /b 1
)
call :colorEcho 02 "Docker containers started."
echo.

:: Step 5: Wait for Healthchecks
call :colorEcho 0E "[5/6] Waiting for services to be healthy..."
timeout /t 30 /nobreak >nul
docker compose ps
echo.

:: Step 6: Display Access Information
call :colorEcho 0E "[6/6] System ready!"
echo.
call :colorEcho 0A "========================================"
call :colorEcho 0A "  Services Running:"
call :colorEcho 0A "========================================"
call :colorEcho 03 "React Dashboard:  http://localhost:5173"
call :colorEcho 03 "Flask API:          http://localhost:5000"
call :colorEcho 03 "PostgreSQL:         localhost:5432"
echo.

:: Auto-open browser
start http://localhost:5173

:: Ask user about optional components
set /p start_simulation="Start attack simulation? (Y/N): "
if /i "!start_simulation!"=="Y" (
    call :colorEcho 0E "Starting attack simulation in new window..."
    start "Attack Simulation" cmd /k "python simulate_attacks.py"
)

set /p start_watcher="Start log watcher for real-time classification? (Y/N): "
if /i "!start_watcher!"=="Y" (
    call :colorEcho 0E "Starting log watcher in new window..."
    start "Log Watcher" cmd /k "python src/log_watcher.py"
)

echo.
call :colorEcho 0A "========================================"
call :colorEcho 0A "  Press Ctrl+C to stop all services"
call :colorEcho 0A "========================================"
echo.

:: Cleanup on exit
:cleanup
echo.
call :colorEcho 0E "Shutting down..."
docker compose down
call :colorEcho 02 "All services stopped."
exit /b 0

:: Color output function
:colorEcho
echo %~2
exit /b 0
