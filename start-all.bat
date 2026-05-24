@echo off
title Full Stack Launcher
echo ============================================
echo   Starting All Services
echo ============================================
echo.

cd /d "%~dp0"

echo Clearing any stale processes on ports 3001, 8001, 3002, 8002...
for %%port in (3001 8001 3002 8002) do (
    for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%%port " ^| findstr "LISTENING"') do (
        taskkill /PID %%p /F >nul 2>&1
    )
)
timeout /t 1 /nobreak >nul

echo [1/4] Pursh Backend   -> http://localhost:8001
start "Pursh Backend :8001" cmd /k "cd /d "%~dp0pursh\backend" && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 1 /nobreak >nul

echo [2/4] AISec Runner    -> http://localhost:8002
start "AISec Runner :8002" cmd /k "cd /d "%~dp0internal\aisec\runner" && python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload --log-level warning"

timeout /t 1 /nobreak >nul

echo [3/4] Pursh Frontend  -> http://localhost:3001
start "Pursh Frontend :3001" cmd /k "cd /d "%~dp0pursh\frontend" && npm run dev"

timeout /t 1 /nobreak >nul

echo [4/4] AISec Dashboard -> http://localhost:3002
start "AISec Dashboard :3002" cmd /k "cd /d "%~dp0internal\aisec\dashboard" && npm run dev"

echo.
echo ============================================
echo   All services launching in separate windows
echo   Pursh app:        http://localhost:3001
echo   Pursh API:        http://localhost:8001
echo   AISec dashboard:  http://localhost:3002
echo   AISec runner:     http://localhost:8002
echo ============================================
echo.
echo Opening browsers in 10 seconds...
timeout /t 10 /nobreak >nul
start "" "http://localhost:3001"
start "" "http://localhost:3002"
