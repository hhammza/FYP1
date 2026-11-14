@echo off
title AMRPredict - Starting Servers
color 0A

echo.
echo  ============================================
echo   AMRPredict - Antibiotic Resistance System
echo  ============================================
echo.

REM   start.bat            backend + React app (web\), installs only what is missing
REM   start.bat --flask    backend + the older Flask app (frontend\) instead
REM   start.bat --update   also reinstall/upgrade dependencies (needs internet)
REM
REM A .venv in the project folder, the backend with DEBUG=True on port 8000,
REM and the React app on port 5173 (Vite) or the Flask app on port 5001
REM (app.py's default; 5000 is avoided because macOS reserves it). A port
REM in use is handled: see "Backend port" below. The venv's python is
REM called directly, so no activation (and no PowerShell execution policy)
REM is needed. Every path is relative to the project folder.

cd /d "%~dp0"

set "UPDATE="
set "UI=react"
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--update" (set "UPDATE=1") else if /i "%~1"=="--flask" (set "UI=flask") else if /i "%~1"=="--react" (set "UI=react") else (
    echo [ERROR] Unknown option: %~1  ^(use --update, --flask^)
    pause
    exit /b 1
)
shift
goto parse_args
:args_done

REM The React app needs Node.js 18+; without it, fall back to the Flask app
if "%UI%"=="react" (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Node.js ^(npm^) not found, so starting the Flask app instead.
        echo        Install Node.js 18+ from nodejs.org for the React app with the Resistance Explorer.
        set "UI=flask"
    )
)

set "VENV=.venv"
set "PY=.venv\Scripts\python.exe"

REM Check Python: the "py" launcher first, then python. Each must have its
REM own standard library (Lib\os.py under its install folder), not just
REM print a version: an incomplete copy of python.exe without its Lib folder
REM still runs, borrowing another install's library and printing "Could not
REM find platform independent libraries" on every start, and a venv made from
REM it breaks when that other install changes.
set "OWNLIB=import os,sys; sys.exit(not os.path.isfile(os.path.join(sys.base_prefix,'Lib','os.py')))"
set "BASEPY="
py -3 -c "%OWNLIB%" >nul 2>&1 && set "BASEPY=py -3"
if not defined BASEPY (python -c "%OWNLIB%" >nul 2>&1 && set "BASEPY=python")

REM A .venv made from such a copy, or from a Python since removed, is rebuilt
if exist "%PY%" (
    "%PY%" -c "%OWNLIB%" >nul 2>&1
    if errorlevel 1 (
        echo [1/5] The existing .venv does not work; rebuilding it...
        rmdir /s /q "%VENV%"
    )
)

if not defined BASEPY if not exist "%PY%" (
    echo [ERROR] No working Python found. Please install Python 3.9+ from python.org
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

if defined UPDATE goto update_deps

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

REM React app packages: installed once (and again with --update)
if not "%UI%"=="react" goto npm_done
if exist "web\node_modules" if not defined UPDATE goto npm_done
echo [3/5] Installing the React app's packages ^(npm ci^)...
pushd web
call npm ci --no-audit --no-fund
if errorlevel 1 (
    echo [WARN] npm ci failed, no internet? Starting the Flask app instead.
    set "UI=flask"
)
popd
:npm_done
if "%UI%"=="react" (set "FRONTEND_PORT=5173") else (set "FRONTEND_PORT=5001")

REM Backend port. If 8000 is taken by this project's backend (an earlier
REM start.bat still open) it is reused; if another program holds it, the
REM backend moves to the next free port and the frontend is pointed there.
REM Our backend's /api/health/ answer has a "models" block; curl ships with
REM Windows 10 and later.
set "BPORT=8000"
set "REUSE_BACKEND="
call :port_busy %BPORT%
if errorlevel 1 goto backend_port_ok
call :is_our_backend %BPORT%
if not errorlevel 1 (
    echo [INFO] The backend is already running on port %BPORT%; using it.
    set "REUSE_BACKEND=1"
    goto backend_port_ok
)
:next_backend_port
set /a BPORT+=1
call :port_busy %BPORT%
if not errorlevel 1 goto next_backend_port
echo [INFO] Port 8000 is used by another program; the backend uses %BPORT%.
:backend_port_ok

REM Frontend port: the next free one if taken
:frontend_port_check
call :port_busy %FRONTEND_PORT%
if errorlevel 1 goto frontend_port_ok
set /a FRONTEND_PORT+=1
goto frontend_port_check
:frontend_port_ok

if defined REUSE_BACKEND goto backend_ready

REM Start Django backend in a new window. DEBUG=True is local development:
REM no SECRET_KEY or ALLOWED_HOSTS needed. To use Train/Reload, first run
REM   set ADMIN_TOKEN=some-password
REM in this window; the Train page then asks for that password.
echo [4/5] Starting Django backend on http://127.0.0.1:%BPORT% ...
cd backend
set DEBUG=True
start "Django Backend (port %BPORT%)" cmd /k "..\%PY% manage.py runserver %BPORT% & pause"
cd ..

REM Wait for Django to answer (loading the models takes a few seconds), up to 60 s
set /a WAITED=0
:wait_backend
call :is_our_backend %BPORT%
if not errorlevel 1 goto backend_ready
set /a WAITED+=1
if %WAITED% geq 60 (
    echo [ERROR] Backend failed to start. See the "Django Backend" window for its error.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait_backend

:backend_ready
if "%UI%"=="react" goto start_react

REM Start Flask frontend in a new window, pointed at the backend's port.
REM PORT stays unset on 5001: app.py then runs in local debug mode (setting
REM PORT means production to it), so it is set only when 5001 is taken.
echo [5/5] Starting Flask frontend on http://127.0.0.1:%FRONTEND_PORT% ...
set "FLASK_PORT_SET="
if not "%FRONTEND_PORT%"=="5001" set "FLASK_PORT_SET=set PORT=%FRONTEND_PORT%& "
cd frontend
start "Flask Frontend (port %FRONTEND_PORT%)" cmd /k "%FLASK_PORT_SET%set BACKEND_URL=http://127.0.0.1:%BPORT%/api& ..\%PY% app.py & pause"
goto frontend_started

:start_react
REM Start the React app in a new window: Vite serves web\ and passes /api
REM through to the backend.
echo [5/5] Starting React frontend on http://127.0.0.1:%FRONTEND_PORT% ...
cd web
start "React Frontend (port %FRONTEND_PORT%)" cmd /k "set API_PROXY=http://127.0.0.1:%BPORT%& npx vite --host 127.0.0.1 --port %FRONTEND_PORT% --strictPort & pause"

:frontend_started

timeout /t 3 /nobreak >nul
cd ..

echo.
echo  ============================================
echo   Both servers started!
echo  ============================================
echo.
echo   Frontend (UI):  http://127.0.0.1:%FRONTEND_PORT%  (%UI% app)
echo   Backend  (API): http://127.0.0.1:%BPORT%/api
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
start "" http://127.0.0.1:%FRONTEND_PORT%

echo.
if defined REUSE_BACKEND (
    echo  Press any key to stop the frontend. The backend belongs to the earlier start.bat and keeps running.
) else (
    echo  Press any key to stop both servers...
)
pause >nul

if not defined REUSE_BACKEND taskkill /fi "WindowTitle eq Django Backend (port %BPORT%)*" /f >nul 2>&1
taskkill /fi "WindowTitle eq Flask Frontend (port %FRONTEND_PORT%)*" /f >nul 2>&1
taskkill /fi "WindowTitle eq React Frontend (port %FRONTEND_PORT%)*" /f >nul 2>&1
echo Servers stopped.
exit /b 0

REM ---- helpers -------------------------------------------------------------
REM errorlevel 0 when something listens on port %1
:port_busy
netstat -ano -p tcp | findstr /r /c:":%1 .*LISTENING" >nul
exit /b %errorlevel%

REM errorlevel 0 when this project's backend answers on port %1
:is_our_backend
curl -s --max-time 3 http://127.0.0.1:%1/api/health/ 2>nul | findstr /c:"\"models\"" >nul
exit /b %errorlevel%
