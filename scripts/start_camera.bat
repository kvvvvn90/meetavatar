@echo off
chcp 65001 >nul
title MeetAvatar Camera Client

cd /d "%~dp0..\camera-client"

set PYTHON=D:\Anaconda3\envs\ai-humanizer\python.exe

:: Check core deps
%PYTHON% -c "import PyQt6, aiohttp, cv2, pyvirtualcam" 2>nul
if %errorlevel% neq 0 (
    echo Installing camera client dependencies...
    %PYTHON% -m pip install -r requirements.txt --quiet
    echo Done.
    echo.
)

echo ============================================
echo   MeetAvatar Camera Client
echo   Local API: http://localhost:18520
echo   Use OBS Virtual Camera in Zoom/Teams
echo ============================================
echo.

%PYTHON% -m camera_client.main --server-url http://localhost:8000

pause
