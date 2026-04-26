@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ========================================
:: ML Honeypot Framework - Clean Shutdown
:: ========================================

echo.
echo ========================================
echo   ML Honeypot Framework - Shutdown
echo ========================================
echo.

:: Admin Check
net session >nul 2>&1
if errorlevel 1 (
    echo [WARN] Not running as Administrator. Firewall rules cleanup will fail.
    echo Please run this script as Administrator to fully clean up mitigation rules.
    echo.
)

:: Step 1: Stop Vite Dev Server
echo [1/3] Stopping Vite Dev Server (node.exe)...
taskkill /F /FI "WINDOWTITLE eq Vite Frontend*" >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo [OK] Vite process terminated (if it was running).
echo.

:: Step 2: Stopping Docker Containers
echo [2/3] Stopping Docker Compose Services...
docker compose down -v --remove-orphans
if errorlevel 1 (
    echo [ERROR] Failed to stop Docker containers.
) else (
    echo [OK] Containers stopped and removed successfully.
)
echo.

:: Step 3: Cleanup Firewall Rules
echo [3/3] Cleaning up Honeypot Firewall Rules...
net session >nul 2>&1
if errorlevel 0 (
    echo [INFO] Executing netsh to clear Honeypot_Block_* rules...
    netsh advfirewall firewall delete rule name=all | findstr /R "Honeypot_Block_" >nul 2>&1
    echo [OK] Firewall rules cleaned (if any existed).
) else (
    echo [SKIP] Skipped firewall cleanup (requires Administrator privileges).
)
echo.

echo ========================================
echo   [OK] System Shutdown Complete
echo ========================================
echo.
echo Note: The 'Live SOC Watcher' and 'Attack Simulation' windows must be closed manually.
echo Press any key to exit.
pause >nul
exit /b 0
