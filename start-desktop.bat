@echo off
title Personal Magazine Desktop
chcp 65001 >nul

echo ==========================================
echo   Personal Magazine - Desktop Launcher
echo ==========================================
echo.

cd /d "%~dp0CampusAI\desktop"

if not exist node_modules (
  echo [1/3] Installing desktop dependencies (first run only)...
  echo       (若下载失败，请先开 Clash 代理 127.0.0.1:7890)
  call npm install
  echo.
) else (
  echo [1/3] Dependencies already installed.
  echo.
)

echo [2/3] Building frontend...
cd /d "%~dp0CampusAI\frontend"
call npm run build
cd /d "%~dp0CampusAI\desktop"
echo.

echo [3/3] Launching desktop app...
echo       (关闭本窗口会退出应用；应用图标在系统托盘)
echo.
call npm start
