@echo off
chcp 65001 >nul
title MeetAvatar - Startup

echo ============================================
echo        MeetAvatar - Starting All Services
echo ============================================
echo.
echo   Mode: Local Development (SQLite, no Docker)
echo.

echo [1/3] Starting FastAPI Backend...
start "MeetAvatar API" "%~dp0scripts\start_api.bat"
echo       Done.
echo.

echo [2/3] Starting React Frontend...
start "MeetAvatar Frontend" "%~dp0scripts\start_frontend.bat"
echo       Done.
echo.

echo [3/3] Starting Camera Client...
start "MeetAvatar Camera" "%~dp0scripts\start_camera.bat"
echo       Done.
echo.

echo ============================================
echo   All services started!
echo ============================================
echo.
echo   Frontend:   http://localhost:5173
echo   API:        http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo   Camera:     System tray icon
echo.
echo   To stop all: run stop.bat or close each window.
echo ============================================
pause
