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
  call npm install
  if errorlevel 1 (
    echo.
    echo [ERROR] npm install 失败，请检查网络/代理后重试。
    pause
    exit /b 1
  )
  echo.
) else (
  echo [1/3] Dependencies already installed.
  echo.
)

echo [2/3] Building frontend...
cd /d "%~dp0CampusAI\frontend"
call npm run build
if errorlevel 1 (
  echo [ERROR] 前端构建失败。
  pause
  exit /b 1
)
cd /d "%~dp0CampusAI\desktop"
echo.

echo [3/3] Launching desktop app...
echo       (应用图标在系统托盘；关闭本窗口会退出应用)
echo.
call npm start
echo.
echo [INFO] 桌面应用已退出。
pause
