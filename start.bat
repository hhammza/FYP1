@echo off
title AMRPredict — Starting Servers
color 0A

echo.
echo  ============================================
echo   AMRPredict — Antibiotic Resistance System
echo  ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Install backend requirements
echo [1/4] Installing backend dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [WARN] Some backend dependencies may not have installed correctly.
)

REM Install frontend requirements
echo [2/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
pip install -r requirements.txt -q

REM Start Django backend in a new window
echo [3/4] Starting Django backend on http://127.0.0.1:8000 ...
cd /d "%~dp0backend"
start "Django Backend (port 8000)" cmd /k "python manage.py runserver 8000 & pause"

REM Wait for Django to start
timeout /t 4 /nobreak >nul

REM Start Flask frontend in a new window
echo [4/4] Starting Flask frontend on http://127.0.0.1:5000 ...
cd /d "%~dp0frontend"
start "Flask Frontend (port 5000)" cmd /k "python app.py & pause"

timeout /t 3 /nobreak >nul

echo.
echo  ============================================
echo   Both servers started!
echo  ============================================
echo.
echo   Frontend (UI):  http://127.0.0.1:5000
echo   Backend  (API): http://127.0.0.1:8000/api
echo.
echo   Opening browser...
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5000

echo.
echo  Press any key to stop both servers...
pause >nul

taskkill /fi "WindowTitle eq Django Backend (port 8000)*" /f >nul 2>&1
taskkill /fi "WindowTitle eq Flask Frontend (port 5000)*" /f >nul 2>&1
echo Servers stopped.
