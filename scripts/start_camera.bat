@echo off
chcp 65001 >nul
title MeetAvatar Camera

cd /d "%~dp0..\camera-client"

:: Activate conda env using full path
call D:\Anaconda3\condabin\conda.bat activate ai-humanizer

:: Install camera client deps if missing
python -c "import pystray" 2>nul
if %errorlevel% neq 0 (
    echo Installing camera client dependencies...
    pip install -r requirements.txt --quiet
    echo Done.
    echo.
)

echo ============================================
echo   MeetAvatar Camera Client
echo   Running in system tray...
echo ============================================
echo.

python -m camera_client.main

pause
