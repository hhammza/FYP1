@echo off
title AMRPredict — Starting Servers
color 0A

echo.
echo  ============================================
echo   AMRPredict — Antibiotic Resistance System
echo  ============================================
echo.

REM   start.bat            start both servers (installs only what is missing)
REM   start.bat --update   also reinstall/upgrade dependencies (needs internet)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Dependencies, checked offline first: "pip install --no-index" succeeds
REM only when every requirement is already installed at a matching version,
REM and never touches the network, so a start with no internet does not
REM hang on pip. Only when something is missing does it go online, with a
REM short timeout; if that fails the servers start anyway with a warning.
REM   start.bat --update   force a full online install and upgrade pip
set "REQS=-r "%~dp0backend\requirements.txt" -r "%~dp0frontend\requirements.txt""
set "PIP=python -m pip --disable-pip-version-check"

if /i "%~1"=="--update" goto update_deps

%PIP% install --no-index %REQS% -q >nul 2>&1
if not errorlevel 1 (
    echo [1/4] Dependencies already installed; skipping, no internet needed.
    goto deps_done
)

echo [1/4] Installing missing dependencies...
%PIP% install --timeout 15 --retries 1 %REQS% -q
if errorlevel 1 (
    echo [WARN] Could not install every dependency, no internet?
    echo        Starting anyway; run "start.bat --update" once you are online.
)
goto deps_done

:update_deps
echo [1/4] Updating dependencies (--update)...
%PIP% install --upgrade pip -q
%PIP% install %REQS% -q
if errorlevel 1 echo [WARN] Some dependencies failed to install.

:deps_done
echo [2/4] Dependencies checked.

REM Start Django backend in a new window. DEBUG=True is local development:
REM no SECRET_KEY or ALLOWED_HOSTS needed. To use Train/Reload, first run
REM   set ADMIN_TOKEN=some-password
REM in this window; the Train page then asks for that password.
echo [3/4] Starting Django backend on http://127.0.0.1:8000 ...
cd /d "%~dp0backend"
set DEBUG=True
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
