@echo off
chcp 65001 >nul

cd /d "%~dp0..\frontend"

if not exist "node_modules" call npm install

echo ============================================
echo   MeetAvatar Frontend
echo   http://localhost:5173
echo ============================================
echo.

title MeetAvatar Frontend
call npm run dev

pause
