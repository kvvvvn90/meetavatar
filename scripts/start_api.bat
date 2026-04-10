@echo off
chcp 65001 >nul
title MeetAvatar API

cd /d "%~dp0..\backend"

if not exist "storage\avatars" mkdir "storage\avatars"

set PYTHON=D:\Anaconda3\envs\ai-humanizer\python.exe

:: Install backend deps if missing
%PYTHON% -c "import pydantic_settings" 2>nul
if %errorlevel% neq 0 (
    echo Installing backend dependencies...
    %PYTHON% -m pip install -r requirements.txt --quiet
    echo Done.
    echo.
)

set MEETAVATAR_MODE=local
set MEETAVATAR_STORAGE_DIR=%cd%\storage
set MEETAVATAR_LIVEPORTRAIT_DIR=%~dp0..\third_party\LivePortrait

echo ============================================
echo   MeetAvatar API Server
echo   http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Database: SQLite (storage/meetavatar.db)
echo ============================================
echo.

%PYTHON% -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
