@echo off
title Personal Magazine Launcher

echo ==========================================
echo   Personal Magazine - one-click launcher
echo ==========================================
echo.

echo [1/2] Starting backend  (http://127.0.0.1:8000) ...
cd /d "%~dp0CampusAI\backend"
start "PM Backend" cmd /k "venv\Scripts\python.exe -m uvicorn main:app --port 8000"

echo [2/2] Starting frontend (http://127.0.0.1:5173) ...
cd /d "%~dp0CampusAI\frontend"
start "PM Frontend" cmd /k "npm run dev"

echo.
echo Backend : http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
echo Open the frontend URL in your browser.
echo.
pause
