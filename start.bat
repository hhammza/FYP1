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
REM
REM A .venv in the project folder, the backend with DEBUG=True on port 8000
REM and the frontend on port 5001 (the recommended ports: app.py's default,
REM and 5000 is avoided because macOS reserves it). The venv's python is
REM called directly, so no activation (and no PowerShell execution policy)
REM is needed. Every path is relative to the project folder.

cd /d "%~dp0"
set "VENV=.venv"
set "PY=.venv\Scripts\python.exe"

REM Check Python: the "py" launcher first, then python
set "BASEPY="
py -3 --version >nul 2>&1 && set "BASEPY=py -3"
if not defined BASEPY (python --version >nul 2>&1 && set "BASEPY=python")
if not defined BASEPY if not exist "%PY%" (
    echo [ERROR] Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

REM Virtual environment
if exist "%PY%" (
    echo [1/5] Using existing virtual environment.
) else (
    echo [1/5] Creating virtual environment in .venv ...
    %BASEPY% -m venv "%VENV%"
    if not exist "%PY%" (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

REM Dependencies, checked offline first: "pip install --no-index" succeeds
REM only when every requirement is already installed at a matching version,
REM and never touches the network, so a start with no internet does not
REM hang on pip. Only when something is missing does it go online, with a
REM short timeout; if that fails the servers start anyway with a warning.
REM   start.bat --update   force a full online install and upgrade pip
set "REQS=-r backend\requirements.txt -r frontend\requirements.txt"
set "PIP="%PY%" -m pip --disable-pip-version-check"

if /i "%~1"=="--update" goto update_deps

%PIP% install --no-index %REQS% -q >nul 2>&1
if not errorlevel 1 (
    echo [2/5] Dependencies already installed; skipping, no internet needed.
    goto deps_done
)

echo [2/5] Installing missing dependencies...
%PIP% install --timeout 15 --retries 1 %REQS% -q
if errorlevel 1 (
    echo [WARN] Could not install every dependency, no internet?
    echo        Starting anyway; run "start.bat --update" once you are online.
)
goto deps_done

:update_deps
echo [2/5] Updating dependencies (--update)...
%PIP% install --upgrade pip -q
%PIP% install %REQS% -q
if errorlevel 1 echo [WARN] Some dependencies failed to install.

:deps_done
echo [3/5] Dependencies checked.

REM Start Django backend in a new window. DEBUG=True is local development:
REM no SECRET_KEY or ALLOWED_HOSTS needed. To use Train/Reload, first run
REM   set ADMIN_TOKEN=some-password
REM in this window; the Train page then asks for that password.
echo [4/5] Starting Django backend on http://127.0.0.1:8000 ...
cd backend
set DEBUG=True
start "Django Backend (port 8000)" cmd /k "..\%PY% manage.py runserver 8000 & pause"

REM Wait for Django to start
timeout /t 4 /nobreak >nul

REM Start Flask frontend in a new window. PORT is left unset on purpose:
REM app.py then runs in local debug mode on 127.0.0.1:5001 only.
echo [5/5] Starting Flask frontend on http://127.0.0.1:5001 ...
cd ..\frontend
start "Flask Frontend (port 5001)" cmd /k "..\%PY% app.py & pause"

timeout /t 3 /nobreak >nul
cd ..

echo.
echo  ============================================
echo   Both servers started!
echo  ============================================
echo.
echo   Frontend (UI):  http://127.0.0.1:5001
echo   Backend  (API): http://127.0.0.1:8000/api
echo.
if defined ADMIN_TOKEN (
    echo   Train/Reload:   on; use your ADMIN_TOKEN as the password on the Train page.
) else (
    echo   Train/Reload:   off. To use them, close this and run:
    echo                   set ADMIN_TOKEN=some-password
    echo                   start.bat
)
echo.
echo   Opening browser...
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5001

echo.
echo  Press any key to stop both servers...
pause >nul

taskkill /fi "WindowTitle eq Django Backend (port 8000)*" /f >nul 2>&1
taskkill /fi "WindowTitle eq Flask Frontend (port 5001)*" /f >nul 2>&1
echo Servers stopped.
