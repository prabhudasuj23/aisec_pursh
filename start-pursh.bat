@echo off
title Pursh Launcher
echo ============================================
echo   Pursh Telehealth App - Starting...
echo ============================================
echo.

cd /d "%~dp0"

echo Clearing any stale processes on ports 8001 and 3001...
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":8001 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":3001 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [1/2] Starting Pursh Backend (port 8001)...
start "Pursh Backend :8001" cmd /k "cd /d "%~dp0pursh\backend" && echo Starting Pursh FastAPI on http://localhost:8001 && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Pursh Frontend (port 3001)...
start "Pursh Frontend :3001" cmd /k "cd /d "%~dp0pursh\frontend" && echo Starting Pursh Next.js on http://localhost:3001 && npm run dev"

echo.
echo ============================================
echo   Pursh is starting up...
echo   Frontend:  http://localhost:3001
echo   Backend:   http://localhost:8001
echo ============================================
echo.
echo Opening browser in 6 seconds...
timeout /t 6 /nobreak >nul
start "" "http://localhost:3001"
