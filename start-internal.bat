@echo off
title AISec Internal Launcher
echo ============================================
echo   AISec Security Dashboard - Starting...
echo ============================================
echo.

cd /d "%~dp0"

echo Clearing any stale processes on ports 8002 and 3002...
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":8002 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":3002 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [1/2] Starting AISec Runner (port 8002)...
start "AISec Runner :8002" cmd /k "cd /d "%~dp0internal\aisec\runner" && echo Starting AISec Runner on http://localhost:8002 && python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload --log-level warning"

timeout /t 2 /nobreak >nul

echo [2/2] Starting AISec Dashboard (port 3002)...
start "AISec Dashboard :3002" cmd /k "cd /d "%~dp0internal\aisec\dashboard" && echo Starting AISec Dashboard on http://localhost:3002 && npm run dev"

echo.
echo ============================================
echo   AISec is starting up...
echo   Dashboard: http://localhost:3002
echo   Runner:    http://localhost:8002
echo ============================================
echo.
echo Opening browser in 8 seconds...
timeout /t 8 /nobreak >nul
start "" "http://localhost:3002"
