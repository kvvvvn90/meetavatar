@echo off
chcp 65001 >nul
title MeetAvatar - Shutdown

echo ============================================
echo        MeetAvatar - Stopping All Services
echo ============================================
echo.

echo [1/3] Stopping API server...
taskkill /fi "WINDOWTITLE eq MeetAvatar API*" /f >nul 2>&1

echo [2/3] Stopping Frontend dev server...
taskkill /fi "WINDOWTITLE eq MeetAvatar Frontend*" /f >nul 2>&1

echo [3/3] Stopping Camera Client...
taskkill /fi "WINDOWTITLE eq MeetAvatar Camera*" /f >nul 2>&1

echo.
echo ============================================
echo   All services stopped.
echo ============================================
pause
